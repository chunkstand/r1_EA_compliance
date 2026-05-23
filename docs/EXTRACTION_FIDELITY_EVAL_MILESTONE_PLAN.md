# Extraction Fidelity Eval Milestone Plan

Date: 2026-05-23

Status: Implementation complete on 2026-05-23. Milestones `0` through `4`
now replay green locally: the live owner split was re-locked from repo
artifacts only, the repo ships `config/extraction_fidelity_eval_v1.json`,
`12` governed fidelity families, `24` tracked cases, fixture-backed
controlled violations, and `tests/test_extraction_fidelity_eval.py` as the
contract substrate, the dedicated `extraction-fidelity-eval` producer writes
durable JSON and Markdown results under
`source_library/evaluations/extraction_fidelity/`, the Docling-backed live
`extraction-accuracy-audit` reran green on
`source-set-f775524ab233ff27` with `581` admitted active-current rows, `0`
blocked rows, and `53` explicit archive/currentness rows, `upstream-eval`
remains narrowed to the capture/catalog umbrella with
`required_lane_count=2`, `required_category_count=8`, `case_count=16`, and
`matched_case_count=16`, and full-canonical `promotion-suite` stays green at
`passed_required_full_canonical_result_count=10`,
`required_full_canonical_result_count=10`,
`full_canonical_source_set_id=source-set-f775524ab233ff27`,
`full_canonical_corpus_ready=true`, and `promotion_ready=true`. The current
green fidelity replay records `matched_case_count=24`,
`parser_route_mismatch_count=1`, `anchor_mismatch_count=13`,
`span_mismatch_count=10`, `boundary_mismatch_count=4`,
`negative_case_pass_count=12`, `negative_case_fail_count=0`, and
`required_check_mismatch_count=0`. The final owner split is now locked:
`diagnostics/extraction_validation.json` remains structural validation,
`diagnostics/extraction_accuracy_audit.json` remains live generated-corpus
truth,
`source_library/evaluations/extraction_fidelity/extraction_fidelity_eval_results.json`
remains the dedicated offline direct-fidelity artifact, and `upstream-eval`
remains the capture/catalog umbrella proof that `promotion-suite` consumes
alongside the live audit. The full canonical source-truth lane is already
resolved locally through `93a23b0`, the downstream full-canonical
compliance-gold lane is already resolved locally through `8e0e02b`, and no
active owner remains in that closed source-truth/gold route. The next routed
owner is now
`docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.
The Milestone `0`/`1` closeout commit is `f2afa8f`
(`Resolve extraction fidelity Milestones 0-1`), the Milestone `2` closeout
commit is `16fb8b2` (`Implement extraction fidelity Milestone 2`), the
Milestone `3` closeout commit is `4269f5e`
(`Implement extraction fidelity Milestone 3`), and the exact Milestone `4`
closeout hash is synced in the immediately following docs-alignment pass.

Owner context: this plan follows
`docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md`, which already created
`upstream-eval` and the upstream coverage register. Milestone `3` in this
packet narrows that older aggregate route so `upstream-eval` now owns only
capture/catalog direct eval while promotion consumes the dedicated extraction
fidelity artifact directly. The repo now has four distinct upstream truth
surfaces:

- `extract-build` structural validation in
  `diagnostics/extraction_validation.json`
- live generated-corpus content audit in
  `diagnostics/extraction_accuracy_audit.json`
- synthetic extraction cases inside `config/upstream_evaluation_v1.json`
- dedicated offline fidelity proof in
  `source_library/evaluations/extraction_fidelity/extraction_fidelity_eval_results.json`

What is still missing is the final live closeout pass that proves the
strengthened upstream/promotion route coexists cleanly with the live
generated-corpus audit. The repo can already prove difficult extraction cases
by span, boundary, layout, scope, parser-route, and negative-case
expectations, and the promotion route now consumes that owner directly.

## Purpose

Raise the import and extraction evaluation standard by adding a dedicated
extraction-fidelity direct-eval lane.

The new lane must prove hard extraction correctness directly:

- not just that the live corpus currently audits green
- not just that the current fixture catalog has one expected pass and one
  controlled violation per category
- not just that downstream retrieval and gold gates stayed green

Instead, the repo should have a governed extraction-fidelity owner that can
fail closed when:

- required text spans disappear
- section boundaries drift
- tables flatten incorrectly
- XML scope extraction leaks or truncates
- parser-route identity changes hide regressions
- wrapper pages are admitted where direct documents are required
- chunk offsets and extracted text no longer agree strongly enough for review

## Current Evidence

- `config/upstream_evaluation_v1.json` now declares only the capture/catalog
  upstream umbrella with `2` required lanes, `8` required categories, and
  `16` fixture-backed cases.
- `tests/test_upstream_evaluation.py` currently proves the real manifest runs
  green with `required_lane_count=2`, `required_category_count=8`,
  `case_count=16`, and `matched_case_count=16`. That confirms the narrowed
  capture/catalog umbrella stays green while extraction direct-eval ownership
  is no longer bundled into the aggregate upstream lane.
- `src/usfs_r1_ea_sources/extraction_accuracy.py` currently owns live
  generated-output checks for:
  `extraction_validation_passed`,
  `required_source_records_are_present_and_direct`,
  `direct_document_required_records_use_document_artifacts`,
  text-file hash parity,
  raw-artifact hash parity,
  chunk/text offset agreement,
  chunk coverage,
  scoped XML accuracy,
  markup leakage,
  and PDF text crosschecks.
- `tests/test_extraction_accuracy.py` already proves important audit behavior,
  including direct-parse admission guards and wrapper-page blocking for direct
  document requirements. Those tests validate the audit owner, while the new
  fidelity command now owns the dedicated offline parser/span/boundary contract.
- Live source-truth on `source-set-f775524ab233ff27` is currently green:
  `extraction_accuracy_audit.json` records `audited_record_count=581`,
  `knowledge_base_admitted_source_record_ids=581`,
  `knowledge_base_blocked_source_record_ids=0`, and
  `explicitly_non_admitted_source_record_ids=53`.
- Live full-canonical promotion is also currently green:
  `promotion_suite_results.json` records
  `full_canonical_corpus_ready=true`,
  `passed_required_full_canonical_result_count=10`,
  `required_full_canonical_result_count=10`, and
  `current_promotion_ready=true`.
- The gap, therefore, is no longer missing source-truth, missing promotion,
  or aggregate-owner routing. The remaining gap is the final live closeout
  replay and docs alignment that proves the strengthened route stays green
  with the live extraction audit.

## Goal

Route the dedicated extraction-fidelity eval producer into the repo's
upstream and promotion truth surfaces.

Success means all of the following are true:

- the repo ships a manifest-owned `extraction-fidelity-eval` command with a
  durable JSON and Markdown output
- the command runs offline from tracked fixtures and controlled violations
- the contract proves fidelity by explicit expectations such as required text
  anchors, boundary spans, table structure retention, parser-route ownership,
  and hard negatives
- the repo keeps the boundary explicit:
  `extraction_validation.json` remains structural validation,
  `extraction_accuracy_audit.json` remains live generated-corpus truth, and
  `extraction_fidelity_eval_results.json` becomes the direct-eval fidelity
  truth
- `upstream-eval` no longer owns raw extraction-fidelity logic directly; it
  must either consume the dedicated summary or route to it explicitly
- the full-canonical readiness route fails closed when the dedicated
  extraction-fidelity artifact is missing, stale, or below threshold

## Non-Goals

- Do not expand `gold-coverage-eval` with resource-area coverage in this
  packet.
- Do not replace or weaken `extraction_accuracy_audit`.
- Do not rerun broad network capture or full download workflows as the normal
  proof path.
- Do not broaden retrieval, claim extraction, rule binding, compliance review,
  or gold adjudication beyond narrow route wiring needed to consume the new
  artifact.
- Do not turn this milestone into a generic parser rewrite.
- Do not stage ignored `source_library/` outputs in git.

## Scope

- dedicated extraction-fidelity contract design
- tracked extraction-fidelity fixtures and controlled-violation inputs
- new extraction-fidelity eval runner, schema, CLI registration, and report
- owner-boundary split between `upstream-eval`, `extraction_accuracy_audit`,
  and the new fidelity command
- readiness and promotion routing for the new fidelity artifact
- focused docs, schema, register, and handoff updates

## Out Of Scope

- workbook capture policy changes
- catalog promotion policy changes outside narrow route integration
- live corpus regeneration as the default proof path
- new downstream semantic evaluation lanes
- review-package-specific adjudication work

## Dependency And Milestone 0 Refresh Rule

- Start this packet from the live docs stack, not from closed gold-lane chat
  history.
- If `docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`, or `config/upstream_evaluation_v1.json`
  drift before implementation starts, Milestone 0 must refresh this plan's
  owner names, counts, and routing before code changes begin.
- If the live full-canonical promotion suite grows beyond the current
  `10/10` full-canonical result count before this packet starts, Milestone 0 must
  update the targeted promotion wiring in this plan rather than preserving
  stale thresholds.
- If implementation cannot keep the owner split explicit between structural
  validation, live audit, and fixture-backed fidelity eval, stop and reroute
  instead of creating overlapping owners.

## Owner Surfaces

- Live extraction audit owner:
  `src/usfs_r1_ea_sources/extraction_accuracy.py`,
  `src/usfs_r1_ea_sources/extraction_admission.py`,
  `src/usfs_r1_ea_sources/extract.py`,
  `tests/test_extraction_accuracy.py`
- Aggregate upstream owner:
  `src/usfs_r1_ea_sources/upstream_evaluation.py`,
  `config/upstream_evaluation_v1.json`,
  `tests/test_upstream_evaluation.py`
- New extraction-fidelity owner:
  `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `config/extraction_fidelity_eval_v1.json`,
  `config/fixtures/extraction_fidelity_eval/`,
  `tests/fixtures/extraction_fidelity_eval/`,
  `tests/test_extraction_fidelity_eval.py`
- Readiness/promotion owner:
  `config/promotion_suite_v1.json`,
  `tests/test_promotion_suite_full_canonical.py`,
  `tests/test_architecture_contract.py`
- Docs and routing owner:
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  this plan,
  `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep live generated-corpus checks in
  `src/usfs_r1_ea_sources/extraction_accuracy.py`. Do not move them into the
  new fidelity-eval module.
- Put the dedicated fixture-backed fidelity producer in a focused new owner
  module, `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`. Do not bury
  its logic across `extract.py`, `extraction_accuracy.py`, and
  `upstream_evaluation.py`.
- Register the new command in `src/usfs_r1_ea_sources/cli_eval.py` with the
  other eval entry points.
- Keep tracked deterministic fixture inputs under
  `config/fixtures/extraction_fidelity_eval/` or
  `tests/fixtures/extraction_fidelity_eval/`; the core command must not depend
  on mutable local `source_library/` state to prove category coverage.
- Write the dedicated results under
  `source_library/evaluations/extraction_fidelity/` so the artifact is clearly
  source-set/global rather than review-local.
- If `upstream-eval` remains the aggregate upstream route, it must consume or
  reference the new extraction-fidelity summary rather than duplicating raw
  extraction fixture ownership.
- The final coverage register should represent:
  `extraction_accuracy` as structural/live audit truth,
  `extraction_fidelity_eval` as direct fidelity truth, and
  `upstream-eval` as the broader upstream umbrella.

## Weak-Point Prevention Contract

- Weak point forecast: the new command simply re-reports
  `extraction_accuracy_audit` booleans, so the fidelity gap survives behind a
  new file name.
  Owner surface:
  `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`,
  `config/extraction_fidelity_eval_v1.json`,
  `tests/test_extraction_fidelity_eval.py`
  Prevention gate: the manifest must require explicit fidelity expectations,
  not only producer pass/fail booleans.
  Fail threshold: the dedicated eval passes while one of its cases lacks a
  text-anchor, span, boundary, layout, scope, parser-route, or negative-case
  expectation.
  Controlled violation: delete the expected anchor/span payload from one
  required case and prove the new eval fails.
  Future-Codex misuse scenario: a later session wraps the live audit and calls
  it "fidelity eval"; manifest-level expectation checks must fail before that
  lands.

- Weak point forecast: the fixture set proves only easy born-digital text and
  misses the difficult parser families that motivated the packet.
  Owner surface:
  `config/extraction_fidelity_eval_v1.json`,
  fixture trees,
  `tests/test_extraction_fidelity_eval.py`
  Prevention gate: the manifest must require category coverage across OCR,
  table-dense PDFs, appendix boundaries, split-page continuations, scoped XML,
  directive documents, forest-plan chapters, forest-plan maps, monitoring
  reports, and direct-document wrapper negatives.
  Fail threshold: the manifest can pass without at least one expected-pass and
  one controlled-violation case for each required fidelity family.
  Controlled violation: remove one required category such as
  `table_structure_fidelity` or `xml_scope_boundary_fidelity`; contract tests
  must fail.
  Future-Codex misuse scenario: a later session keeps only the easiest HTML or
  statute fixtures; the category floor must fail.

- Weak point forecast: normalization becomes so loose that missing text still
  passes, or so strict that harmless formatting churn blocks valid output.
  Owner surface:
  `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`,
  `tests/test_extraction_fidelity_eval.py`
  Prevention gate: the contract must define allowed normalization and the test
  suite must include one near-match that should pass and one paraphrased or
  truncated match that must fail.
  Fail threshold: a paraphrased or materially incomplete extraction still
  counts as a pass, or harmless whitespace/case noise fails the whole lane.
  Controlled violation: mutate a case from exact anchor retention to a loose
  paraphrase and prove failure.
  Future-Codex misuse scenario: a later session broadens normalization to hide
  parser regressions; the controlled violation must catch it.

- Weak point forecast: parser-route drift hides fidelity loss by silently
  swapping one parser family for another.
  Owner surface:
  `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`,
  `src/usfs_r1_ea_sources/extract.py`,
  `tests/test_extraction_fidelity_eval.py`
  Prevention gate: required cases must carry expected parser-route metadata
  where parser identity is load-bearing.
  Fail threshold: a case passes after switching from its expected parser route
  to another route without explicit contract approval.
  Controlled violation: change a tracked case from its expected parser route
  and prove the eval fails.
  Future-Codex misuse scenario: a later session swaps in a weaker fallback
  parser that still returns some text; parser-route identity must expose it.

- Weak point forecast: the repo lands a strong new command but leaves routing
  and operator truth unchanged, so promotion still stays green without the new
  artifact.
  Owner surface:
  `config/promotion_suite_v1.json`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`
  Prevention gate: promotion and register wiring must fail closed on missing,
  stale, or below-threshold extraction-fidelity artifacts, and the routed docs
  must name the new owner explicitly.
  Fail threshold: the milestone lands but the active promotion route can remain
  green without any extraction-fidelity result.
  Controlled violation: remove the dedicated result from a controlled test
  manifest and prove the suite/register contract fails.
  Future-Codex misuse scenario: a later session updates the command only and
  forgets the readiness route; the docs and suite checks must catch it.

## Milestone Sequence

### Milestone 0 - Freshness And Owner-Boundary Lock

Outcome label: `resolved`

Purpose: lock the live baseline and decide the final owner split before new
code is written.

Implementation tasks:

1. Re-run the read-only grounding pass for:
   `config/upstream_evaluation_v1.json`,
   `src/usfs_r1_ea_sources/upstream_evaluation.py`,
   `src/usfs_r1_ea_sources/extraction_accuracy.py`,
   `tests/test_upstream_evaluation.py`,
   `tests/test_extraction_accuracy.py`,
   `docs/EVALUATION_COVERAGE_REGISTER.md`,
   `docs/CURRENT_ROUTING.md`,
   `docs/CURRENT_SYSTEM_STATE.md`,
   and `docs/SESSION_HANDOFF.md`.
2. Freeze the target owner split in code and docs:
   `extraction_validation.json` = structural validation,
   `extraction_accuracy_audit.json` = live generated-output audit,
   `extraction_fidelity_eval_results.json` = fixture-backed direct fidelity,
   `upstream-eval` = upstream umbrella that references the dedicated fidelity
   owner instead of owning raw extraction fixtures directly.
3. Lock the live baseline counts and route facts that later docs must preserve:
   upstream eval still green,
   extraction audit still green,
   full-canonical promotion still green at `10/10`.

Required verification:

```bash
git status -sb
rg -n "extraction_accuracy|upstream-eval|direct_eval_present|source-set-f775524ab233ff27" README.md docs/CURRENT_ROUTING.md docs/CURRENT_SYSTEM_STATE.md docs/SESSION_HANDOFF.md docs/EVALUATION_COVERAGE_REGISTER.md config/upstream_evaluation_v1.json tests/test_upstream_evaluation.py tests/test_extraction_accuracy.py
git diff --check
```

Milestone 0 closeout note on 2026-05-23:

- The repo-grounded refresh found no drift in the planned owner split, no
  drift in the live full-canonical baseline, and no reason to reopen the
  resolved source-truth or downstream gold lanes.

### Milestone 1 - Contract And Fixture Substrate

Outcome label: `resolved`

Purpose: create the governed extraction-fidelity contract before command
implementation.

Implementation tasks:

1. Add `config/extraction_fidelity_eval_v1.json` with:
   - manifest identity and schema version
   - required fidelity category IDs
   - minimum expected-pass and controlled-violation counts per category
   - expected output schema fields
   - expected parser-route metadata where route identity is load-bearing
2. Add tracked fixture families under
   `config/fixtures/extraction_fidelity_eval/` or
   `tests/fixtures/extraction_fidelity_eval/`.
3. Add failing-or-baseline contract tests in
   `tests/test_extraction_fidelity_eval.py`.

Minimum required fidelity families:

- `ocr_anchor_fidelity`
- `table_structure_fidelity`
- `appendix_boundary_fidelity`
- `section_boundary_fidelity`
- `statute_scope_fidelity`
- `directive_document_fidelity`
- `forest_plan_chapter_fidelity`
- `forest_plan_map_label_fidelity`
- `monitoring_report_fidelity`
- `split_page_continuation_fidelity`
- `parser_route_identity`
- `direct_document_wrapper_negative`

Acceptance signals:

- missing categories fail closed
- out-of-tree or review-local fixtures fail closed
- each required category has both an expected-pass and a controlled-violation
  case

Required verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_extraction_fidelity_eval.py -q
git diff --check
```

Milestone 1 closeout note on 2026-05-23:

- `config/extraction_fidelity_eval_v1.json` now defines `12` required
  fidelity families and `24` tracked cases.
- `config/fixtures/extraction_fidelity_eval/` now contains one tracked
  expected-pass plus one controlled-violation scenario for each required
  family.
- `tests/test_extraction_fidelity_eval.py` now proves the real manifest,
  missing-category fail-closed behavior, and out-of-tree fixture fail-closed
  behavior.
- The Milestone `0`/`1` closeout commit is
  `f2afa8f` (`Resolve extraction fidelity Milestones 0-1`).

### Milestone 2 - Dedicated Extraction-Fidelity Eval Producer

Outcome label: `resolved`

Purpose: implement the command, schema, and report that turn the contract into
durable direct-eval truth.

Implementation tasks:

1. Add `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`.
2. Register `extraction-fidelity-eval` in
   `src/usfs_r1_ea_sources/cli_eval.py`.
3. Write a durable results artifact and Markdown report under
   `source_library/evaluations/extraction_fidelity/`.
4. Record explicit metrics such as:
   required category count,
   case count,
   matched expectation count,
   failed case IDs,
   category summaries,
   parser-route mismatches,
   anchor/span mismatch counts,
   boundary mismatch counts,
   and negative-case pass/fail outcomes.
5. Add controlled-violation tests for:
   missing anchors,
   wrong boundary spans,
   wrong parser route,
   over-loose normalization,
   and direct-document wrapper false positives.

Acceptance signals:

- the command runs fully offline from tracked fixtures
- the command fails closed on controlled violations
- the results schema is stable enough for routing and docs consumption

Required verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_extraction_fidelity_eval.py tests/test_extraction_accuracy.py tests/test_architecture_contract.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/extraction_fidelity_eval.py src/usfs_r1_ea_sources/cli_eval.py tests/test_extraction_fidelity_eval.py tests/test_extraction_accuracy.py tests/test_architecture_contract.py
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources extraction-fidelity-eval --manifest config/extraction_fidelity_eval_v1.json --output-dir source_library
git diff --check
```

Milestone 2 closeout note on 2026-05-23:

- `src/usfs_r1_ea_sources/extraction_fidelity_eval.py` now owns the dedicated
  offline fixture replay, manifest validation, fidelity metrics, and durable
  JSON/Markdown outputs under
  `source_library/evaluations/extraction_fidelity/`.
- `src/usfs_r1_ea_sources/cli_eval.py` now registers
  `extraction-fidelity-eval`, and the architecture/output-schema docs now
  carry the new command and artifact owner.
- The current green replay on the committed manifest records
  `required_category_count=12`, `case_count=24`, `matched_case_count=24`,
  `parser_route_mismatch_count=1`, `anchor_mismatch_count=13`,
  `span_mismatch_count=10`, `boundary_mismatch_count=4`, and
  `negative_case_pass_count=12`.
- The Milestone `2` closeout commit is `16fb8b2`
  (`Implement extraction fidelity Milestone 2`).
- Next routing: execute Milestone `3` in this packet to narrow the older
  upstream extraction umbrella and make the new artifact load-bearing in
  upstream/promotion truth.

### Milestone 3 - Upstream And Promotion Routing Integration

Outcome label: `resolved`

Purpose: make the new producer load-bearing instead of optional.

Implementation tasks:

1. Update `src/usfs_r1_ea_sources/upstream_evaluation.py` and
   `config/upstream_evaluation_v1.json` so the upstream umbrella no longer owns
   raw extraction fidelity fixtures directly.
2. Decide and implement one routed path:
   - either `upstream-eval` consumes
     `source_library/evaluations/extraction_fidelity/extraction_fidelity_eval_results.json`
   - or the coverage register and promotion suite route extraction fidelity
     directly and `upstream-eval` narrows to capture/catalog only
3. Update `config/promotion_suite_v1.json` so full-canonical readiness fails
   closed on missing, stale, or below-threshold extraction-fidelity results.
4. Update the coverage register so the final owner split is explicit and
   future sessions do not reopen the closed gold lane to solve an upstream
   extraction problem.

Acceptance signals:

- the new artifact is load-bearing in the routed readiness path
- the register and promotion docs no longer imply that `upstream-eval` alone
  is sufficient extraction direct-eval truth

Required verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_upstream_evaluation.py tests/test_promotion_suite_full_canonical.py tests/test_architecture_contract.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/upstream_evaluation.py tests/test_upstream_evaluation.py tests/test_promotion_suite_full_canonical.py tests/test_architecture_contract.py
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json --output-dir source_library
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
git diff --check
```

Milestone 3 closeout note on 2026-05-23:

- `upstream-eval` no longer owns raw extraction fidelity fixtures; the real
  manifest now stays green with `required_lane_count=2`,
  `required_category_count=8`, `case_count=16`, and
  `matched_case_count=16` across the capture/catalog umbrella only.
- `promotion-suite` now requires
  `source_library/evaluations/extraction_fidelity/extraction_fidelity_eval_results.json`
  directly as a full-canonical result and stays green at
  `passed_required_full_canonical_result_count=10`,
  `required_full_canonical_result_count=10`.
- The Milestone `3` closeout commit is `4269f5e`
  (`Implement extraction fidelity Milestone 3`).
- The owner split is now explicit:
  `extraction_validation.json` = structural validation,
  `extraction_accuracy_audit.json` = live generated-corpus truth,
  `extraction_fidelity_eval_results.json` = direct extraction fidelity truth,
  `upstream-eval` = capture/catalog umbrella only.
- Next routing: execute Milestone `4` in this packet to rerun the live audit
  plus the strengthened upstream/promotion route and finish packet
  closeout/alignment.

### Milestone 4 - Live Closeout And Alignment

Outcome label: `resolved`

Closeout update on 2026-05-23:

- `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources extraction-fidelity-eval --manifest config/extraction_fidelity_eval_v1.json --output-dir source_library`
  reran green at `required_category_count=12`, `case_count=24`,
  `matched_case_count=24`, `parser_route_mismatch_count=1`,
  `anchor_mismatch_count=13`, `span_mismatch_count=10`,
  `boundary_mismatch_count=4`, `negative_case_pass_count=12`,
  `negative_case_fail_count=0`, and `required_check_mismatch_count=0`.
- `PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library`
  reran green on `source-set-f775524ab233ff27` with
  `audited_record_count=581`, `audited_chunk_count=96997`,
  `knowledge_base_admitted_source_record_ids=581`,
  `knowledge_base_blocked_source_record_ids=0`, and
  `explicitly_non_admitted_source_record_ids=53`.
- `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json --output-dir source_library`
  reran green at `required_lane_count=2`, `required_category_count=8`,
  `case_count=16`, and `matched_case_count=16`.
- `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
  reran green at `passed_required_full_canonical_result_count=10`,
  `required_full_canonical_result_count=10`,
  `full_canonical_source_set_id=source-set-f775524ab233ff27`,
  `full_canonical_corpus_ready=true`, `current_promotion_ready=true`,
  `expansion_ready=true`, and `promotion_ready=true`.
- The next routed owner is now
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`;
  the exact Milestone `4` closeout hash is synced in the immediately
  following docs-alignment pass.

Purpose: prove the new direct-eval owner coexists cleanly with the live
source-truth and promotion route.

Implementation tasks:

1. Re-run the dedicated extraction-fidelity eval on the committed fixture
   contract.
2. Re-run the live `extraction-accuracy-audit` on
   `source-set-f775524ab233ff27`.
3. Re-run the upstream umbrella and full-canonical promotion route.
4. Update the routed docs and this plan with the exact closeout hash,
   resulting counts, and final owner split.
5. Commit the verified implementation slice atomically.

Acceptance signals:

- the new fidelity eval is green
- the live extraction audit remains green
- the upstream umbrella remains truthful
- the promotion route remains green and now consumes the stronger upstream
  fidelity proof

Required verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources extraction-fidelity-eval --manifest config/extraction_fidelity_eval_v1.json --output-dir source_library
PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json --output-dir source_library
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
PYTHONPATH=src .venv/bin/python -m pytest tests/test_extraction_fidelity_eval.py tests/test_extraction_accuracy.py tests/test_upstream_evaluation.py tests/test_promotion_suite_full_canonical.py tests/test_architecture_contract.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/extraction_fidelity_eval.py src/usfs_r1_ea_sources/upstream_evaluation.py src/usfs_r1_ea_sources/cli_eval.py tests/test_extraction_fidelity_eval.py tests/test_extraction_accuracy.py tests/test_upstream_evaluation.py tests/test_promotion_suite_full_canonical.py tests/test_architecture_contract.py
git diff --check
```

## Required Implementation Artifacts

- `config/extraction_fidelity_eval_v1.json`
- `config/fixtures/extraction_fidelity_eval/` or
  `tests/fixtures/extraction_fidelity_eval/`
- `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`
- `src/usfs_r1_ea_sources/cli_eval.py`
- `tests/test_extraction_fidelity_eval.py`
- any focused updates required in:
  `src/usfs_r1_ea_sources/upstream_evaluation.py`,
  `tests/test_upstream_evaluation.py`,
  `config/upstream_evaluation_v1.json`,
  `config/promotion_suite_v1.json`,
  `tests/test_promotion_suite_full_canonical.py`

## Required Documentation And Handoff Updates

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

The final closeout must record:

- the exact command surface for `extraction-fidelity-eval`
- the final owner split between validation, live audit, and direct fidelity
- the exact live result used by promotion
- the closeout commit hash
- any remaining accepted risk and next routed owner

## Required Verification Gates

- Contract and fixture tests for missing categories, out-of-tree fixtures, and
  controlled violations
- Focused extraction-audit regressions proving the live audit owner remains
  intact
- Upstream umbrella verification showing truthful routing after the owner split
- Full-canonical promotion verification proving the new artifact is load
  bearing
- `tests/test_architecture_contract.py` because a new public eval command and
  config owner will be added
- `git diff --check`

## Acceptance Criteria

- A dedicated `extraction-fidelity-eval` command exists, writes a durable
  artifact, and runs offline from tracked fixtures.
- The dedicated contract requires both expected-pass and controlled-violation
  coverage for every required fidelity family.
- The dedicated artifact records fidelity-specific metrics rather than only
  producer pass/fail booleans.
- `extraction_accuracy_audit` remains the live generated-corpus truth surface
  and is not weakened or replaced.
- The final coverage register and routed docs name the final owner split
  explicitly.
- The final readiness route fails closed when the new extraction-fidelity
  artifact is missing, stale, or below threshold.
- All required docs and handoff surfaces are updated in the same milestone
  closeout commit.
- Anti-test-weakening rule: do not weaken tests, add skips, loosen
  assertions, lower thresholds, or reduce negative coverage just to make the
  new fidelity lane go green. Any replacement coverage must keep the same or
  higher negative-case count, and the Milestone 2 and Milestone 4 `pytest`
  commands must still prove that controlled-violation cases fail closed.

## Stop Conditions

- Stop if the only implementable design simply repackages
  `extraction_accuracy_audit` without new fixture-backed fidelity assertions.
- Stop if the packet would require live network fetches or broad corpus
  regeneration as the normal proof path.
- Stop if the packet cannot keep validation, live audit, and direct-eval
  ownership distinct.
- Stop if promotion wiring would require reopening the closed source-truth or
  downstream gold packets instead of a narrow upstream route update.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no milestone in this plan may be marked
  complete, `resolved`, or `reduced` until required verification passes and
  the local atomic commit exists. Before that point, the slice is
  ready-to-close, not complete.
- Replacement coverage must be equivalent or stronger.
- Treat each milestone as incomplete until its verification passes and a local
  atomic commit exists.
- Stage only the verified milestone slice.
- Leave unrelated dirty or ignored files alone.
- Include implementation, tests, docs, config updates, and handoff updates for
  the completed milestone in the same commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Stop before committing if required verification fails or the slice cannot be
  separated cleanly.

## Residual Risks And Next Routing

- Even after this packet closes, live extraction can still drift in ways that
  no finite fixture set covers. That residual risk remains owned jointly by
  `extraction_accuracy_audit`, the verified extraction admission contract, and
  the new fixture refresh discipline.
- If the new fidelity command proves a broader parser-route or fixture-refresh
  maintenance burden than expected, route that as a narrow follow-on under the
  same owner rather than reopening downstream gold breadth work.
- If import accuracy, rather than extraction fidelity, becomes the next weak
  point after this closes, the follow-on owner should be a separate capture or
  catalog integrity packet, not an expansion of this extraction plan.

## Closeout Checklist

- [x] Milestone 0 rechecked the live owner split and route facts
- [x] `config/extraction_fidelity_eval_v1.json` exists with governed required categories
- [x] tracked fidelity fixtures and controlled violations exist
- [x] `extraction-fidelity-eval` is implemented and CLI-registered
- [x] dedicated results and report artifacts are documented
- [x] `upstream-eval` and promotion wiring consume the new owner truthfully
- [x] `README.md`, routing docs, current-state docs, this plan, and handoff are aligned
- [x] focused tests, lint, eval commands, and `git diff --check` passed
- [ ] closeout commit hash is recorded in `docs/SESSION_HANDOFF.md`
