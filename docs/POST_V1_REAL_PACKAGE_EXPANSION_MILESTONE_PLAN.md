# Post-V1 Real-Package Expansion Milestone Plan

Date: 2026-05-06
Status: in progress; Sequences 0 and 1 complete; Sequence 2 artifact pass exposed ECID
source-claim and forest-plan component blockers

## Weakness

Broader post-V1 expansion is not ready. The Sequence 0 promotion-suite baseline reported
`expansion_ready=false` because:

- the ECID preliminary-EA expansion slot is blocked by `adjudication_needed`; and
- the third real-package expansion slot is still `package_fixture_missing`.

Sequence 1 closed the ECID applicability-adjudication blocker locally. Sequence 2 then generated
and validated the ECID rule pack, ran compliance review and review-scoped phase eval, generated a
forest-plan component adjudication worklist, and added promotion-suite expansion artifact checks.
That pass removed the ECID `adjudication_needed` blocker but correctly did not mark the slot ready.
The follow-up expert-panel alignment review found one manifest gap: the ECID compliance artifact
recorded `17` rule-claim gaps, but the promotion suite accepted that count as expected. Those gaps
now block expansion as `missing_source` until every applicable generated rule has cited
source-claim support. ECID compliance review also fails reviewer readiness on
`forest_plan_component_gate_reviewer_ready` because `29` applicable Forest Plan standards were
identified, only `7` were applied, and the component worklist contains `158`
missing-package-evidence rows. The third real-package expansion slot still remains
`package_fixture_missing`.

The current V1 Custer Gallatin proving review remains promoted. This plan resolves the broader
expansion weakness without weakening the current source-record, document-role, citation,
forest-plan, phase-eval, applicability-validation, generated-rule-pack, compliance-review, or
promotion-suite gates.

## Goal

Make the post-V1 promotion suite report `expansion_ready=true` and make strict expansion promotion
pass for the declared real-package expansion set.

Completion means:

- `current_promotion_ready=true`
- `expansion_ready=true`
- `promotion_ready=true` under `--strict-expansion`
- `failure_category_counts={}`
- `expansion_failure_category_counts={}`
- `open_expansion_slot_count=0`

## Non-Goals

- Do not claim full Region 1 production readiness from two or three packages.
- Do not mark an expansion slot `ready=true` from a manifest edit alone.
- Do not use model-written prose as an adjudication substitute.
- Do not convert ignored `source_library/` generated outputs into tracked files unless repository
  policy changes.
- Do not add a new forest profile unless profile-specific source readiness, component inventory,
  and eval coverage are part of that same milestone slice.

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
Artifact pass complete as of 2026-05-06, but reviewer-ready acceptance is blocked by source-claim
gap closure and Forest Plan component adjudication. The ECID applicability-derived rule pack
validates with `46` generated rules. Compliance review wrote the expected ECID review artifacts but
reported `rule_claim_gap_count=17`, `reviewer_ready=false`, and `validation_passed=false` because
source-claim support is incomplete and `forest_plan_component_gate_reviewer_ready` failed.
Review-scoped phase eval wrote
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
- Compliance review: wrote all expected artifacts, but reports `rule_claim_gap_count=17` and fails
  reviewer readiness because `forest_plan_component_gate_reviewer_ready` failed. Authority
  applicability, generated-pack, source-set, matrix, PDF, non-applicable authority,
  authority-resolution, litigation-risk, and finding-graph checks were present.
- Phase eval: failed with `14/15` phases passing; blockers were
  `compliance_review/phase_validation_failed` and `compliance_review/phase_not_reviewer_ready`.
- Promotion suite non-strict: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `expansion_artifacts_ready=false`, `failure_category_counts={}`,
  and `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 5,
  "missing_source": 1, "package_fixture_missing": 1}`.
- Promotion suite strict expansion: expected failure with `promotion_ready=false` and
  `failure_category_counts={"forest_plan_reviewer_not_ready": 5, "missing_source": 1,
  "package_fixture_missing": 1}`.

### Sequence 2A: ECID Source-Claim Gap Closure

Purpose: close the ECID rule-claim evidence blocker exposed by Sequence 2 before treating the
expansion package as reviewer-ready.

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

### Sequence 2B: ECID Forest Plan Component Adjudication

Purpose: close the ECID reviewer-ready blocker exposed by Sequence 2 without weakening the Forest
Plan component gate.

Actions:

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

### Sequence 3: Third Real-Package Fixture Contract

Purpose: replace `package_fixture_missing` with a concrete third real-package fixture and a typed
readiness contract.

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

### Sequence 4: Third Package Applicability-First Run

Purpose: run the complete applicability-first sequence on the third package and either close or
type every blocker.

Actions:

- Run package context build, applicability retrieval, applicability determination, validation, and
  adjudication as needed.
- Generate the rule pack only after validation passes.
- Run compliance review and phase eval only after generated-rule-pack validation passes.
- If the package exposes a general extraction, retrieval, source, graph, or forest-profile defect,
  fix the general method and add eval coverage before marking the slot ready.

Acceptance:

- Third package has a passing applicability validation and generated rule pack, or a typed blocker
  that is accepted as the next milestone and leaves `expansion_ready=false`.
- To close this weakness, the third package must reach reviewer-ready status and the slot must be
  marked ready only after artifact checks pass.

### Sequence 5: Strict Expansion Promotion Closeout

Purpose: prove broader expansion readiness using the same promotion-suite contract agents will use
in later sessions.

Actions:

- Run the full focused and strict promotion verification stack.
- Update `docs/POST_V1_PROMOTION_SUITE.md`, `docs/CURRENT_SYSTEM_STATE.md`, `README.md`, and
  `docs/SESSION_HANDOFF.md` with exact run results.
- Commit implementation, manifest, tests, and docs as one verified milestone slice.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --strict-expansion

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

## Stop Conditions

- An adjudication cannot be replayed from the adjudication eval artifact.
- A slot would need to be marked ready by assertion rather than verified artifacts.
- A new package requires an unimplemented forest profile or missing source coverage.
- Applicability validation fails on stale, missing, unsupported, duplicated, or unresolved
  decisions after adjudication.
- Generated rule-pack creation would require bypassing validation.
- Compliance review or phase eval fails for a reason outside the current sequence boundary.
- Strict expansion can pass while an expansion slot still has typed blockers.
