# Post-V1 Real-Package Expansion Milestone Plan

Date: 2026-05-06
Status: in progress; Sequences 0 and 1 complete

## Weakness

Broader post-V1 expansion is not ready. The Sequence 0 promotion-suite baseline reported
`expansion_ready=false` because:

- the ECID preliminary-EA expansion slot is blocked by `adjudication_needed`; and
- the third real-package expansion slot is still `package_fixture_missing`.

Sequence 1 has since closed the ECID applicability-adjudication blocker locally. The remaining ECID
work is Sequence 2: generate the ECID rule pack, run compliance review and phase eval, and update
the promotion-suite expansion signal from verified artifacts. The third real-package expansion slot
still remains `package_fixture_missing`.

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

Actions:

- Generate and validate the ECID applicability-derived rule pack.
- Run compliance review with the generated rule pack and `--reuse-package-cache`.
- Run phase eval for `region1-expansion-ecid-preliminary-ea`.
- Add promotion-suite artifact checks for the ECID expansion review if the manifest does not yet
  verify those artifacts directly.
- Mark the ECID expansion slot ready only after the artifact checks pass.

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
```

Acceptance:

- Generated rule-pack validation passes.
- Compliance review summary reports `reviewer_ready=true`.
- Phase eval passes all required phases for the ECID expansion review.
- Promotion suite has no ECID `adjudication_needed` expansion blocker.

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
