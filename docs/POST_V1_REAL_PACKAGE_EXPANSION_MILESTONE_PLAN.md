# Post-V1 Real-Package Expansion Milestone Plan

Date: 2026-05-06
Status: Resolved 2026-05-14 (complete through Sequence 7 plus South Plateau adjudication/replay
closeout; the declared ECID preliminary-EA and South Plateau expansion set is now green on fresh
non-strict and strict `promotion-suite` replay)

Closeout note: the tracked `31`-item South Plateau forest-plan component adjudication queue is now
closed as `applicability_false_positive` system misses, South Plateau review-scoped `phase-eval`
now passes `19/19` with `contract_backed_promotion_ready=true`, the ad hoc ECID expansion
`phase-eval` replay is refreshed on `source-set-ba8d0feae79501b8` with
`declared_review_contract=false`, and fresh promotion-suite replays now report
`current_promotion_ready=true`, `expansion_ready=true`, and `promotion_ready=true`. The next
follow-on packet is outside this plan; if the queued stack resumes, start with Milestone `0` in
`docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`.

## Owner Surfaces

- promotion manifest owner:
  `config/promotion_suite_v1.json`
- review-contract owners:
  `config/v1_south_plateau_real_ea_eval.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/gold_coverage_v1.json`,
  `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`, and
  `config/forest_plan_component_adjudications/region1-expansion-south-plateau-landscape-treatment.json`
- generated review/artifact owners:
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/` and
  `source_library/reviews/region1-expansion-south-plateau-landscape-treatment/`
- durable routing owners:
  `README.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md`, and
  `docs/SESSION_HANDOFF.md`

## Weak-Point Prevention Contract

- Weak point forecast: a future session may treat the South Plateau reviewer-ready conversion as a
  docs-only manifest edit, skip the ECID ba8d replay refresh, or weaken gold/coverage thresholds
  until strict expansion turns green without truthful review artifacts.
- Owner surface: the expansion truth owner remains
  `config/promotion_suite_v1.json` plus the tracked South Plateau and real-package coverage
  contracts listed above; the closeout must continue to fail closed there.
- Controlled violation: if South Plateau drifts back to pending adjudications, stale replay
  surfaces, or typed blocker semantics, the promotion manifest and its focused tests must fail
  rather than silently preserving green status.
- Future-Codex misuse scenario: a later agent may try to remove `phase_eval_declared_review_contract`
  or reviewer-ready slot checks to avoid refreshing old ECID/South Plateau artifacts. This plan
  prevents that by requiring live replay-backed closeout, not manifest-only edits.
- Anti-test-weakening rule: do not lower thresholds, delete blocker categories, or remove
  reviewer-ready gates just to force expansion green. Do not weaken tests, contract checks, or
  eval thresholds to manufacture a pass. Coverage changes must stay truthful to the live package
  set.
- Complete-after-commit rule: a sequence or milestone is not complete until the required runtime
  replay, focused verification, durable docs/handoff updates, and one local commit all land
  together.
- Atomic commit rule: stage only the verified expansion slice for that milestone; do not fold in
  unrelated viewer/demo, downloader, or adjacent forest work.

## Weakness

Broader post-V1 expansion was not ready at the Sequence 0 baseline. The promotion-suite baseline
originally reported `expansion_ready=false` because:

- the ECID preliminary-EA expansion slot is blocked by `adjudication_needed`; and
- the third real-package expansion slot was still `package_fixture_missing`.

Sequence 1 closed the ECID applicability-adjudication blocker locally. Sequence 2 then generated
and validated the ECID rule pack, ran compliance review and review-scoped phase eval, generated a
forest-plan component adjudication worklist, and added promotion-suite expansion artifact checks.
That pass removed the ECID `adjudication_needed` blocker but correctly did not mark the slot ready.
The follow-up expert-panel alignment review found one manifest gap: the ECID compliance artifact
recorded `17` rule-claim gaps, but the promotion suite accepted that count as expected. Sequence 2A
closed that source-claim gap by fixing rule-claim topic matching for generated authority-family
topic slugs. ECID now reports `rule_claim_gap_count=0`, `rule_claim_link_count=211`, and no
`missing_source` promotion-suite blocker. Sequence 2B then completed the `158`-row Forest Plan
component adjudication replay over the existing ECID package cache. The adjudication eval resolves
all `158` rows as true EA package-evidence omissions with `0` system misses, compliance review now
reports `reviewer_ready=true`, and review-scoped phase eval passes. Sequence 3 replaced the
unknown third-package placeholder with the selected South Plateau fixture contract. Sequence 4
imported the South Plateau package and ran the applicability-first path through validation.
Sequence 5 then resolved the six South Plateau authority-family positive/negative trigger
conflicts through replayable adjudication and reran validation. Sequence 6 generated and validated
the South Plateau rule pack, ran compliance review and review-scoped phase eval, added South
Plateau artifact checks to the promotion suite, and marked the slot ready after those generated
review checks passed. Sequence 7 then found and closed the remaining declared-profile gate by
making South Plateau strict expansion fail closed while forest-plan context is ambiguous.
The 2026-05-07 South Plateau forest-plan context pass resolved that ambiguous context to
`scope_status="custer_gallatin"` with context validation passing. The slot remains blocked because
forest-plan component evaluation now exposes `31` pending `missing_package_evidence` adjudications.

A follow-up artifact review found that the South Plateau slot could still pass strict expansion while
its forest-plan context is unresolved: the slot declares `forest_plan_profile="custer_gallatin"`,
but `compliance_review.json` records `forest_plan_review.scope_status="ambiguous"`,
`forest_plan_review.validation_passed=false`, `forest_plan_review.reviewer_ready=false`, and
`forest_plan_review.needs_reviewer_resolution=true`. Review-scoped `phase-eval` still passes, but
Sequence 7 now prevents strict expansion promotion from passing unless the declared forest-plan
profile resolves or the slot carries the typed blocker.

The current V1 Custer Gallatin proving review remains promoted. This plan resolves the broader
expansion weakness without weakening the current source-record, document-role, citation,
forest-plan, phase-eval, applicability-validation, generated-rule-pack, compliance-review, or
promotion-suite gates.

## Goal

Make the post-V1 promotion suite report broader expansion readiness only when declared real-package
slots and their required artifacts are genuinely ready, including declared forest-plan context.

Completion means the current V1 promotion remains green and expansion readiness is explicit:

- `current_promotion_ready=true`
- non-strict `promotion_ready=true`
- strict `promotion_ready=true` only when `expansion_ready=true`
- strict `promotion_ready=false` with typed failure categories when any declared expansion slot is
  selected but not reviewer-ready
- no current-promotion regression while expansion-only blockers are resolved or carried explicitly

Sequence 7 narrows this completion claim: strict expansion may only pass for South Plateau if the
declared Custer Gallatin forest-plan context is resolved and reviewer-ready, or if the slot is no
longer ready and strict expansion fails with a typed `forest_plan_reviewer_not_ready` blocker. The
2026-05-07 follow-up met that typed-blocker condition by resolving context and making the component
adjudication queue the only remaining forest-plan blocker.

## Non-Goals

- Do not claim full Region 1 production readiness from two or three packages.
- Do not mark an expansion slot `ready=true` from a manifest edit alone.
- Do not use model-written prose as an adjudication substitute.
- Do not convert ignored `source_library/` generated outputs into tracked files unless repository
  policy changes.
- Do not add a new forest profile unless profile-specific source readiness, component inventory,
  and eval coverage are part of that same milestone slice.
- Do not treat an ambiguous forest-plan context as non-applicable simply because the compliance
  matrix currently has zero Forest Plan rows.

## Current Inputs

- Promotion suite manifest: `config/promotion_suite_v1.json`
- Promotion runbook/status: `docs/POST_V1_PROMOTION_SUITE.md`
- Applicability-first parent plan: `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md`
- ECID expansion review ID: `region1-expansion-ecid-preliminary-ea`
- ECID package path:
  `source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)/Preliminary Environmental Assessment`
- ECID source set: `source-set-ba8d0feae79501b8`
- Sequence 0 ECID unresolved families:
  `cultural_resource_protection_and_state_shpo_sources`,
  `minerals_energy_authorities`, and
  `species_supporting_sources_and_overlays`

## Milestone Sequence

### Sequence 0: Expansion Baseline Lock

Purpose: prove the current failure is exactly the two expected expansion blockers before changing
fixtures, adjudication records, or promotion manifest state.

Status:
Complete as of 2026-05-06. The baseline lock was run without adjudicating ECID, adding a third
package fixture, or changing the promotion manifest.

Baseline evidence:

- Non-strict promotion-suite output:
  `source_library/reviews/promotion_suite/sequence0-baseline-nonstrict/promotion_suite_results.json`
- Strict promotion-suite output:
  `source_library/reviews/promotion_suite/sequence0-baseline-strict/promotion_suite_results.json`
- Non-strict result: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `failure_category_counts={}`,
  `expansion_failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`,
  and `open_expansion_slot_count=2`.
- Strict result: expected command failure with `current_promotion_ready=true`,
  `promotion_ready=false`, `expansion_ready=false`,
  `failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`,
  `expansion_failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`,
  and `open_expansion_slot_count=2`.
- At the Sequence 0 baseline, the ECID adjudication worklist had exactly three pending items:
  `cultural_resource_protection_and_state_shpo_sources`,
  `minerals_energy_authorities`, and `species_supporting_sources_and_overlays`.

Actions:

- Run the normal promotion suite and strict expansion suite.
- Confirm the non-strict suite keeps current promotion ready.
- Confirm strict expansion fails only on `adjudication_needed` and `package_fixture_missing`.
- Inspect the ECID adjudication template/worklist and record the three unresolved authority family
  IDs in the handoff.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --strict-expansion
```

Acceptance:

- Non-strict `promotion_ready=true`.
- Strict expansion fails only because `expansion_ready=false`.
- Expansion blockers are limited to one `adjudication_needed` slot and one
  `package_fixture_missing` slot.

### Sequence 1: ECID Adjudication Closure

Purpose: resolve the three ECID preliminary-EA positive/negative authority conflicts with a
replayable adjudication record.

Status:
Complete as of 2026-05-06. The three pending ECID adjudication items were completed as
`human_applicable`, evaluated, applied to the decision ledger, and validated.

Closure evidence:

- `applicability-adjudication-eval`: passed with `3` resolved adjudications, `0` pending
  adjudications, and `failure_category_counts={}`.
- `applicability-adjudication-apply`: passed with `applied_item_count=3` and
  `remaining_unresolved_authority_count=0`.
- `applicability-validate`: passed with `46` applicable authorities, `346` non-applicable
  authorities, `0` unresolved, `0` `needs_adjudication`, `generated_rule_pack_ready=true`, and
  `reviewer_ready=true`.
- The applied decision-ledger hash is
  `207f2c17c8e13708dc46b6b50581183f5ea6af523cc3aeb76d585557fcfb77cd`.

Actions:

- Complete the ECID `applicability_adjudication_template.json` for the three unresolved authority
  families.
- Run `applicability-adjudication-eval` against the completed file.
- Apply the adjudication with `applicability-adjudication-apply`.
- Rerun `applicability-validate`.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-eval \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id source-set-ba8d0feae79501b8 \
  --adjudication-file source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/applicability_adjudication_template.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-apply \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id source-set-ba8d0feae79501b8 \
  --adjudication-file source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/applicability_adjudication_template.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id source-set-ba8d0feae79501b8
```

Acceptance:

- Adjudication eval passes.
- Adjudication apply records `human_adjudication` bases.
- Applicability validation passes with no unresolved or `needs_adjudication` decisions.

### Sequence 2: ECID Reviewer-Ready Expansion Review

Purpose: convert the adjudicated ECID preliminary-EA applicability run into a generated rule pack,
compliance review, phase-eval pass, and promotion-suite expansion signal.

Status:
Artifact pass complete as of 2026-05-06, but reviewer-ready acceptance is blocked by Forest Plan
component adjudication. The ECID applicability-derived rule pack validates with `46` generated
rules. Sequence 2A closed the earlier source-claim gap, so compliance review now reports
`rule_claim_gap_count=0` and `rule_claim_link_count=211`. Compliance review still reports
`reviewer_ready=false` and `validation_passed=false` because
`forest_plan_component_gate_reviewer_ready` failed. Review-scoped phase eval wrote
`source_library/reviews/region1-expansion-ecid-preliminary-ea/phase_eval_results.json` and failed
only the `compliance_review` phase, with `14/15` phases passing. The generated Forest Plan
component adjudication worklist has `158` pending rows.

Actions:

- Generate and validate the ECID applicability-derived rule pack.
- Run compliance review with the generated rule pack and `--reuse-package-cache`.
- Run phase eval for `region1-expansion-ecid-preliminary-ea`.
- Add promotion-suite artifact checks for the ECID expansion review if the manifest does not yet
  verify those artifacts directly.
- Mark the ECID expansion slot ready only after the artifact checks pass.
- If source-claim or Forest Plan component validation fails, keep the ECID slot blocked with typed
  `missing_source` or `forest_plan_reviewer_not_ready` signals and generate the corresponding
  worklist instead of substituting model-written adjudication.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)/Preliminary Environmental Assessment" \
  --output-dir source_library \
  --rule-pack source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/generated_rule_pack.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id region1-expansion-ecid-preliminary-ea \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-template \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea
```

Acceptance:

- Generated rule-pack validation passes.
- Compliance review summary reports `reviewer_ready=true`, unless the sequence exposes typed
  source-claim or Forest Plan component blockers that must become the next ECID sequence.
- Phase eval passes all required phases for the ECID expansion review, unless the same typed
  blockers are present.
- Promotion suite has no ECID `adjudication_needed` expansion blocker.

Sequence 2 latest local result:

- Generated rule-pack validation: passed, `generated_rule_count=46`.
- Compliance review: wrote all expected artifacts, reports `rule_claim_gap_count=0` and
  `rule_claim_link_count=211`, and fails reviewer readiness because
  `forest_plan_component_gate_reviewer_ready` failed. Authority applicability, generated-pack,
  source-set, matrix, PDF, non-applicable authority, authority-resolution, litigation-risk, and
  finding-graph checks were present.
- Phase eval: failed with `14/15` phases passing; blockers were
  `compliance_review/phase_validation_failed` and `compliance_review/phase_not_reviewer_ready`.
- Promotion suite non-strict: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `expansion_artifacts_ready=false`, `failure_category_counts={}`,
  and `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 5,
  "package_fixture_missing": 1}`.
- Promotion suite strict expansion: expected failure with `promotion_ready=false` and
  `failure_category_counts={"forest_plan_reviewer_not_ready": 5, "package_fixture_missing": 1}`.

### Sequence 2A: ECID Source-Claim Gap Closure

Purpose: close the ECID rule-claim evidence blocker exposed by Sequence 2 before treating the
expansion package as reviewer-ready.

Status:
Complete as of 2026-05-06. Rule-claim topic matching now treats generated authority-family topic
slugs as compatible with exact source-record matches, so catalog human-label topic text no longer
creates false `explicit_no_claim_gap` records. ECID generated rule-claim binding now links all `46`
generated rules with `211` rule-claim links and `0` gaps.

Actions:

- Inspect the `17` `explicit_no_claim_gap` rows in
  `source_library/derived/source-set-ba8d0feae79501b8/rule_claim_links/generated-nepa-ea-v0-region1-expansion-ecid-preliminary-ea/applicability-v0/rule_claim_link_gaps.jsonl`.
- Close each gap by improving source-claim extraction, source-claim binding, retrieval/source
  evidence coverage, or by carrying an explicit typed source-coverage blocker when the source
  library lacks usable authority evidence.
- Rerun ECID compliance review with the generated ECID rule pack and `--reuse-package-cache`.
- Rerun non-strict and strict promotion suite checks.

Acceptance:

- ECID compliance review reports `rule_claim_gap_count=0`.
- The promotion suite has no ECID `missing_source` expansion artifact blocker.
- Any remaining ECID blocker is limited to typed Forest Plan component adjudication evidence, not
  missing source-claim support for applicable generated rules.

Sequence 2A latest local result:

- `rule-claim-link` for the ECID generated rule pack: passed with `linked_rule_count=46`,
  `link_count=211`, `gap_count=0`, and `reviewer_ready=true`.
- ECID `compliance-review`: expected command failure remains, but the summary reports
  `rule_claim_gap_count=0`; the only failed validation check is
  `forest_plan_component_gate_reviewer_ready`.
- ECID review-scoped `phase-eval`: expected command failure remains with `14/15` phases passing;
  the `rule_claim_binding` phase is reviewer-ready with `gap_count=0`.
- Promotion suite non-strict: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `expansion_artifacts_ready=false`, `failure_category_counts={}`, and
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 5,
  "package_fixture_missing": 1}`.

### Sequence 2B: ECID Forest Plan Component Adjudication

Status: complete as of 2026-05-06. The ECID Forest Plan component adjudication eval passed against
the current `158`-row queue with `resolved_adjudication_count=158`, `real_ea_omission_count=158`,
`pending_adjudication_count=0`, and `system_miss_count=0`. ECID compliance review now reports
`reviewer_ready=true`, the ECID review-scoped phase eval passes, and the promotion suite has no ECID
`forest_plan_reviewer_not_ready`, `missing_source`, or `adjudication_needed` blocker. The sequence
closeout gap pass tightened the adjudication artifact contract so resolved items preserve compact
component/source trace references, including source-record IDs, citations, hashes, chunk IDs, pages,
and offsets/text spans when available; resolved adjudications now fail eval if those trace
references are dropped.

Purpose: close the ECID reviewer-ready blocker exposed by Sequence 2 without weakening the Forest
Plan component gate.

Actions:

- Preserve the existing ECID package cache and source-set artifacts; do not rerun full corpus,
  download, or extraction workflows unless a freshness/hash gate requires it.
- Complete the generated `forest_plan_component_adjudication_template.json` as a reviewer
  adjudication file, classifying each of the `158` missing-package-evidence rows with an allowed
  disposition.
- Run `forest-plan-component-adjudication-eval` against the completed file.
- Rerun ECID compliance review with the generated ECID rule pack and `--reuse-package-cache`.
- Rerun review-scoped phase eval for `region1-expansion-ecid-preliminary-ea`.
- Rerun non-strict and strict promotion suite checks.
- Mark the ECID expansion slot ready only if compliance validation, matrix readiness, review-scoped
  phase eval, and the ECID expansion artifact checks all pass.

Acceptance:

- Forest Plan component adjudication eval passes and matches the current `158`-row queue.
- ECID compliance review reports `reviewer_ready=true`.
- ECID review-scoped phase eval reports `passed=true` and `reviewer_ready=true`.
- Promotion suite has no ECID `forest_plan_reviewer_not_ready` or `adjudication_needed` expansion
  blocker.

Expert-panel alignment checks:

- Scott Vandegrift: keep this as a targeted replay over the existing ECID cache and make readiness
  status explicit through the Forest Plan component eval, compliance validation, phase eval, and
  promotion-suite gates.
- Chuck Nicholson: treat the `158` rows as practitioner QA/QC work items; every accepted
  disposition must explain whether the package supplies component evidence or whether the row is a
  true package-evidence omission.
- Liz Esposito: preserve component IDs, source-record IDs, package citations, source citations,
  hashes/offsets/pages when available, and keep any unresolved or missing evidence visible instead
  of converting it into a legal conclusion.

### Sequence 3: Third Real-Package Fixture Contract

Purpose: replace `package_fixture_missing` with a concrete third real-package fixture and a typed
readiness contract.

Status:
Complete as of 2026-05-06. `region1-real-ea-slot-2` now selects the South Plateau Area Landscape
Treatment Project as `region1-expansion-south-plateau-landscape-treatment`, records official
project/document-page metadata, declares the local package intake path, keeps the package inside the
promoted `custer_gallatin` forest-plan profile, lists the expected package/applicability/generated
rule/compliance/phase-eval artifacts, and reports a typed `applicability_miss` blocker until the
package is imported and run. Normal promotion remains current-ready; strict expansion fails only on
that typed not-run slot. The Sequence 3 gap-close pass makes that contract fail-closed: selected
not-ready slots must keep review ID, package path, source set, expected gate artifacts, next action,
and a non-`package_fixture_missing` failure category; ready slots cannot retain a failure category;
and promotion-suite Markdown now displays selected-slot review/package/failure metadata.

Actions:

- Select a real Region 1 EA package that adds coverage beyond the promoted V1 review and the ECID
  preliminary EA.
- Prefer a package that exercises different document shape, package evidence quality, authority
  triggers, and Forest Plan issues. If it requires a new forest profile, add source readiness and
  profile/component eval coverage first.
- Add the package fixture metadata to `config/promotion_suite_v1.json`.
- Add or update tests so the promotion suite distinguishes a missing package fixture from a
  present-but-not-ready package.
- Keep any unresolved applicability as typed readiness blockers, not silent failure.

Acceptance:

- The third slot is no longer `package_fixture_missing`.
- The manifest identifies the review ID, package path, source set, expected gate artifacts, and
  next action for any remaining typed blocker.
- Focused promotion-suite tests pass.

Latest local result:

- Selected package: South Plateau Area Landscape Treatment Project, Custer Gallatin National
  Forest, Hebgen Lake Ranger District, project `57353`.
- Review ID: `region1-expansion-south-plateau-landscape-treatment`.
- Declared package path:
  `source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment`.
- Non-strict promotion suite: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `expansion_artifacts_ready=true`,
  `expansion_failure_category_counts={"applicability_miss": 1}`, and
  `open_expansion_slot_count=1`.
- Strict expansion suite: expected command failure with `promotion_ready=false` and
  `failure_category_counts={"applicability_miss": 1}`.
- Gap-close verification: `tests/test_promotion_suite.py` plus
  `tests/test_architecture_contract.py` passed with `16` tests; `ruff check src tests`,
  `compileall src`, JSON validation, `git diff --check`, non-strict promotion suite, and expected
  strict expansion failure all passed.

### Sequence 4: Third Package Applicability-First Run

Purpose: run the complete applicability-first sequence on the third package and either close or
type every blocker.

Status:
Complete as of 2026-05-06. The official South Plateau project package was imported and the
applicability-first path ran through validation. Validation exposed a typed adjudication blocker,
so generated rule-pack creation, compliance review, and review-scoped phase eval were correctly not
run.

Actions:

- Import the official South Plateau project documents into
  `source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment`.
- Run package context build, applicability retrieval, applicability determination, validation, and
  adjudication as needed.
- Generate the rule pack only after validation passes.
- Run compliance review and phase eval only after generated-rule-pack validation passes.
- If the package exposes a general extraction, retrieval, source, graph, or forest-profile defect,
  fix the general method and add eval coverage before marking the slot ready.

Acceptance:

- Third package has a passing applicability validation and generated rule pack, or a typed blocker
  that is accepted as the next milestone and leaves `expansion_ready=false`.

Latest local result:

- Imported `26` official PDFs from the South Plateau project Box folder into
  `source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment`; the ignored
  intake manifest records `70,145,951` bytes.
- Package cache build with `.venv-docling`: `26/26` files extracted, `0` failed, `3,671` chunks,
  parser counts `docling=25` and `pypdf_text_fallback=1`; `ea-review` returned
  `reviewer_ready=true` for the package cache/checklist gate.
- `applicability-authority-universe`: passed with `392` candidates.
- `applicability-context-build`: passed package fact graph validation for `3,671` chunks.
- `applicability-retrieve`: passed trace validation and retained diagnostics for all `392`
  candidates (`low_confidence_retrieval`, `retrieval_miss`, and `excessive_graph_fan_out`).
- `applicability-determine`: `55` applicable authorities, `331` non-applicable authorities, and
  `6` `needs_adjudication` authorities; `generated_rule_pack_ready=false`.
- `applicability-validate`: expected command failure with `passed=false`, `reviewer_ready=false`,
  `generated_rule_pack_ready=false`, `failure_category_counts={"unresolved_authority": 12}`, and
  `6` unresolved/needs-adjudication authorities.
- `applicability-adjudication-template`: wrote
  `source_library/reviews/region1-expansion-south-plateau-landscape-treatment/applicability/applicability_adjudication_template.json`
  and matching worklist with `6` pending items.
- The promotion-suite slot now carries `failure_category="adjudication_needed"` and remains
  `ready=false`.
- Non-strict promotion-suite rerun: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `expansion_artifacts_ready=true`, `failure_category_counts={}`,
  `expansion_failure_category_counts={"adjudication_needed": 1}`,
  `open_expansion_artifact_count=0`, and `open_expansion_slot_count=1`.
- Strict expansion promotion-suite rerun: expected command failure with `promotion_ready=false` and
  `failure_category_counts={"adjudication_needed": 1}`.

Sequence 5 resolved authority-family adjudication items:

- `cultural_resource_protection_and_state_shpo_sources`
- `invasive_pesticide_soils_farmland_drinking_water`
- `roads_access_special_use_action_authorities`
- `species_supporting_sources_and_overlays`
- `vegetation_wildfire_forest_health_authorities`
- `wilderness_wsr_trails_designated_areas`

### Sequence 5: South Plateau Applicability Adjudication Closure

Purpose: resolve the six South Plateau applicability conflicts with a replayable adjudication
record, then rerun validation before any generated-rule or compliance-review work.

Status:
Complete as of 2026-05-06. The six pending South Plateau adjudication items were completed as
`human_applicable`, evaluated, applied to the decision ledger, and validated.

Closure evidence:

- `applicability-adjudication-eval`: passed with `6` resolved adjudications, `0` pending
  adjudications, and `failure_category_counts={}`.
- `applicability-adjudication-apply`: passed with `applied_item_count=6`,
  `remaining_unresolved_authority_count=0`, and applied decision-ledger hash
  `09b9558edf24dbf5ea53e10420c1d8826f212feab4415099ada400cf6d697515`.
- `applicability-validate`: passed with `61` applicable authorities, `331` non-applicable
  authorities, `0` unresolved, `0` `needs_adjudication`, `generated_rule_pack_ready=true`, and
  `reviewer_ready=true`.
- The promotion-suite slot now carries `failure_category="generated_rule_pack_pending"` and
  remains `ready=false` because generated rule-pack validation, compliance review, and
  review-scoped phase eval have not run for South Plateau.

Actions:

- Complete
  `source_library/reviews/region1-expansion-south-plateau-landscape-treatment/applicability/applicability_adjudication_template.json`
  for the six pending authority-family conflicts.
- Run `applicability-adjudication-eval`.
- Apply the adjudication with `applicability-adjudication-apply`.
- Rerun `applicability-validate`.
- Only if validation passes, continue to generated rule-pack validation, compliance review, and
  review-scoped phase eval in the next sequence.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment \
  --source-set-id source-set-ba8d0feae79501b8 \
  --adjudication-file source_library/reviews/region1-expansion-south-plateau-landscape-treatment/applicability/applicability_adjudication_template.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-apply \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment \
  --source-set-id source-set-ba8d0feae79501b8 \
  --adjudication-file source_library/reviews/region1-expansion-south-plateau-landscape-treatment/applicability/applicability_adjudication_template.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment \
  --source-set-id source-set-ba8d0feae79501b8
```

Acceptance:

- Adjudication eval passes with no pending items.
- Adjudication apply records replayed adjudication bases and leaves `0` unresolved authorities.
- Applicability validation passes with no `needs_adjudication` decisions and
  `generated_rule_pack_ready=true`.
- To close this weakness, the third package must reach reviewer-ready status and the slot must be
  marked ready only after artifact checks pass.

### Sequence 6: South Plateau Generated Review And Strict Expansion Promotion Closeout

Purpose: generate and validate the South Plateau rule pack, run compliance review and review-scoped
phase eval, then prove broader expansion readiness using the same promotion-suite contract agents
will use in later sessions.

Status:
Complete as of 2026-05-06. South Plateau generated rule-pack validation, compliance review,
matrix/PDF output, review-scoped phase eval, and promotion-suite strict expansion all passed. The
Sequence 6 promotion manifest included South Plateau as a required expansion review case, so strict
expansion checked the generated rule pack, compliance validation, compliance matrix/PDF, authority
sidecars, litigation-risk summary, and review-scoped phase eval directly before reporting
`promotion_ready=true`. Sequence 7 supersedes the Sequence 6 strict-readiness result by adding the
declared forest-plan profile gate and blocking South Plateau with `forest_plan_reviewer_not_ready`.

Closure evidence:

- `applicability-generate-rule-pack`: passed with `61` generated rules,
  `generated_rule_pack_ready=true`, and generated pack hash
  `39663183f91ad309fcfad60a17d0d88b371e184df8f06664cadd612b5c7aebec`.
- `compliance-review`: passed with `reviewer_ready=true`, `validation_passed=true`, `61`
  findings, `41` pass, `19` uncertain, `1` gap, `280` rule-claim links, and `0` rule-claim gaps.
- `phase-eval --review-id region1-expansion-south-plateau-landscape-treatment`: passed `15/15`
  phases with `reviewer_ready=true` at Sequence 6 closeout; the later Sequence 7 rerun passes
  `16/16` after the NEPA 3D source-set graph phase became available.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: rerun after the South Plateau
  review-scoped eval to restore the shared current-promotion phase artifact; passed `17/17`.
- Strict `promotion-suite` written to
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion/`:
  `current_promotion_ready=true`, `promotion_ready=true`, `expansion_ready=true`,
  `expansion_artifacts_ready=true`, `failure_category_counts={}`,
  `expansion_failure_category_counts={}`, `open_expansion_artifact_count=0`, and
  `open_expansion_slot_count=0`. This is retained as Sequence 6 historical evidence, not the
  current strict expansion signal after Sequence 7.
- Non-strict `promotion-suite` was rerun last and reports the same readiness with
  `strict_expansion=false`.
- Sequence 6 alignment pass: ECID and South Plateau ready-slot `expected_gate_artifacts` now cover
  their matching `required_for_expansion` review-case artifact IDs, and manifest validation rejects
  ready expansion slots that omit those checked artifacts.

Actions:

- Generate the South Plateau applicability rule pack from the validated `61` applicable authorities.
- Validate the generated rule pack against the current South Plateau applicability artifacts.
- Run South Plateau compliance review, compliance validation, matrix/PDF generation, and
  review-scoped phase eval.
- Mark the South Plateau expansion slot ready only if those artifacts pass.
- Run the full focused and strict promotion verification stack.
- Update `docs/POST_V1_PROMOTION_SUITE.md`, `docs/CURRENT_SYSTEM_STATE.md`, `README.md`, and
  `docs/SESSION_HANDOFF.md` with exact run results.
- Commit implementation, manifest, tests, and docs as one verified milestone slice.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment \
  --output-dir source_library \
  --rule-pack source_library/reviews/region1-expansion-south-plateau-landscape-treatment/applicability/generated_rule_pack.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id region1-expansion-south-plateau-landscape-treatment \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion \
  --strict-expansion

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py tests/test_applicability_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/promotion_suite_v1.json /tmp/promotion_suite_v1.validated.json
git diff --check
```

Acceptance:

- Strict promotion suite reports `promotion_ready=true`.
- `expansion_ready=true`.
- Expansion failure categories are empty.
- Handoff states the exact package set and residual boundary.

### Sequence 7: South Plateau Forest-Plan Gate Boundary Closure

Purpose: make strict expansion promotion fail closed when a ready expansion slot declares a
forest-plan profile but the generated review artifacts do not resolve that profile to a
reviewer-ready forest-plan context.

Status:
Complete as of 2026-05-06. This gate-hardening and South Plateau closeout sequence did not weaken
the applicability, generated-rule, compliance-review, phase-eval, or current promotion-suite gates
that already pass. It added the missing forest-plan condition to the expansion readiness contract
and blocks South Plateau strict expansion with `forest_plan_reviewer_not_ready`.

Closure evidence:

- `config/promotion_suite_v1.json` marks
  `region1-expansion-south-plateau-landscape-treatment` as
  `status="blocked_forest_plan_review"`, `ready=false`, and
  `failure_category="forest_plan_reviewer_not_ready"`, while preserving
  `forest_plan_profile="custer_gallatin"`.
- The same slot's `last_local_signal` still records `forest_plan_scope_status="ambiguous"` and
  `forest_plan_component_gate_required=false`; the runtime profile check requires that signal to
  match the artifact rather than pretending it is resolved.
- `source_library/reviews/region1-expansion-south-plateau-landscape-treatment/compliance_review.json`
  records `summary.reviewer_ready=true`, but its nested `summary.forest_plan_review` records
  `scope_status="ambiguous"`, `validation_passed=false`, `reviewer_ready=false`, and
  `needs_reviewer_resolution=true`.
- `source_library/reviews/region1-expansion-south-plateau-landscape-treatment/phase_eval_results.json`
  passes `16/16` phases with `reviewer_ready=true`, so phase eval does not by itself surface the
  declared-profile mismatch.
- Strict expansion promotion now fails as expected with
  `failure_category_counts={"forest_plan_reviewer_not_ready": 3}` while
  `current_promotion_ready=true`.

Actions:

1. Add a regression fixture for the current false-pass shape: a selected expansion slot with
   `ready=true`, `forest_plan_profile="custer_gallatin"`, passing compliance/phase artifacts, and
   nested `forest_plan_review.scope_status="ambiguous"` must not produce
   `expansion_ready=true`.
2. Extend the promotion-suite expansion contract so any ready slot with `forest_plan_profile` must
   have review-case artifact checks for forest-plan context readiness. At minimum, the checks must
   prove:
   - `summary.forest_plan_review.scope_status` matches the declared profile;
   - `summary.forest_plan_review.validation_passed=true`;
   - `summary.forest_plan_review.reviewer_ready=true`;
   - the slot's recorded `last_local_signal.forest_plan_scope_status` matches the artifact; and
   - if Forest Plan component evaluation is required, phase eval sees the component eval or
     component-adjudication phase before reporting reviewer readiness.
3. Resolve South Plateau's forest-plan path using general profile/package evidence, not a hidden
   one-off South Plateau exception. Preferred closure is for the package to resolve to Custer
   Gallatin, rerun compliance review with `--reuse-package-cache`, and produce reviewer-ready
   forest-plan context and any required component/standard evidence. If the package cannot be
   defensibly resolved within this sequence, mark the slot `ready=false` with
   `failure_category="forest_plan_reviewer_not_ready"` and a concrete next action.
4. Rerun South Plateau review-scoped `phase-eval` and strict plus non-strict promotion suite. Strict
   expansion must either pass with a resolved/reviewer-ready forest-plan context or fail with only
   the typed forest-plan blocker.
5. Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, this plan, `docs/POST_V1_PROMOTION_SUITE.md`
   if the promotion-suite contract changes, and `docs/SESSION_HANDOFF.md` with the exact final
   state.

Verification:

```bash
jq '.summary.forest_plan_review' \
  source_library/reviews/region1-expansion-south-plateau-landscape-treatment/compliance_review.json

jq '{passed, reviewer_ready, phase_count, passed_phase_count, phases: [.phases[].name]}' \
  source_library/reviews/region1-expansion-south-plateau-landscape-treatment/phase_eval_results.json

PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py
PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_forest_plan_resolver.py tests/test_forest_plan_components.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion \
  --strict-expansion

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/promotion_suite_v1.json /tmp/promotion_suite_v1.validated.json
git diff --check
```

Acceptance:

- A ready expansion slot with a declared forest-plan profile cannot pass strict expansion while the
  nested `forest_plan_review` is ambiguous, failed, stale, or not reviewer-ready.
- South Plateau either:
  - resolves to `custer_gallatin`, carries reviewer-ready forest-plan context and any required
    component/standard evidence, passes review-scoped phase eval, and passes strict promotion; or
  - remains blocked with `ready=false`, `failure_category="forest_plan_reviewer_not_ready"`, a
    concrete `next_action`, and strict promotion fails without any unrelated current-promotion
    regression.
- The promotion-suite report names the forest-plan blocker explicitly instead of hiding it behind a
  passing compliance-review or phase-eval summary.
- Current V1 promotion remains green for `v1-cg-ecid-compliance-review`.

Sequence 7 latest local result, updated by the 2026-05-07 South Plateau context pass:

- Regression fixtures in `tests/test_promotion_suite.py` prove a manifest `ready=true` false-pass
  shape with ambiguous nested forest-plan context cannot produce `expansion_ready=true`, a selected
  forest-profile slot cannot omit `forest_plan_context_summary` from expected gate artifacts, and a
  slot that records `forest_plan_component_gate_required=true` cannot pass without a
  `forest_plan_component_eval` or `forest_plan_component_adjudication` phase.
- South Plateau forest-plan context resolves to `scope_status="custer_gallatin"` with
  `validation_passed=true`, `2` geographic areas, `9` management areas, `4` overlays, and `5`
  supporting-plan routes.
- South Plateau forest-plan component evaluation records `329` components, `152` applicable
  components, `24` applicable standards, `21` applied standards, and `31` pending
  `missing_package_evidence` adjudication items.
- South Plateau review-scoped phase eval is now `15/17` with blockers limited to
  `compliance_review` and `forest_plan_component_adjudication`; promoted V1 review-scoped phase
  eval was restored at `20/20`.
- Non-strict promotion suite: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `expansion_artifacts_ready=false`, `failure_category_counts={}`,
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
  `open_expansion_artifact_count=5`, and `open_expansion_slot_count=1`.
- Strict expansion promotion suite: expected command failure with `current_promotion_ready=true`,
  `promotion_ready=false`, `expansion_ready=false`,
  `failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`, and no unrelated
  current-promotion regression.

Next implementation pass:

Complete `source_library/reviews/region1-expansion-south-plateau-landscape-treatment/forest_plan_component_adjudication_template.json`
as `forest_plan_component_adjudication.json`, run `forest-plan-component-adjudication-eval`, then
rerun South Plateau compliance review, South Plateau phase eval, promoted V1 phase eval, strict
promotion, and non-strict promotion.

Stop conditions:

- The resolver cannot distinguish South Plateau package location/profile evidence from generic
  references to Custer Gallatin plan analysis.
- The fix would mark `forest_plan_profile` optional for ready slots or remove the South Plateau
  declared profile to make promotion pass.
- Strict expansion still passes while `forest_plan_review.scope_status="ambiguous"` for a ready
  declared-profile slot.
- Closing the package requires new source capture, a new Region 1 forest profile, or a full corpus
  rebuild outside this sequence.

## Stop Conditions

- An adjudication cannot be replayed from the adjudication eval artifact.
- A slot would need to be marked ready by assertion rather than verified artifacts.
- A new package requires an unimplemented forest profile or missing source coverage.
- Applicability validation fails on stale, missing, unsupported, duplicated, or unresolved
  decisions after adjudication.
- Generated rule-pack creation would require bypassing validation.
- Compliance review or phase eval fails for a reason outside the current sequence boundary.
- Strict expansion can pass while an expansion slot still has typed blockers.
