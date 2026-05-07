# South Plateau Forest-Plan Context Milestone Plan

Date: 2026-05-07
Status: planned / active next implementation pass

This plan resolves the remaining strict-expansion blocker for the South Plateau Area Landscape
Treatment Project without weakening the generated applicability, generated rule-pack, compliance,
phase-eval, or promotion-suite gates that already pass.

## Goal

Resolve `region1-expansion-south-plateau-landscape-treatment` to reviewer-ready Custer Gallatin
forest-plan context if the package and profile evidence support that result. If the evidence does
not support reviewer-ready context, keep the expansion slot blocked with a typed
`forest_plan_reviewer_not_ready` failure and a more specific next action.

Completion means:

- current V1 promotion remains green;
- ECID expansion remains ready;
- South Plateau either passes strict expansion with validated Custer Gallatin forest-plan context,
  or remains explicitly blocked for a narrower forest-plan reason;
- the resolver improvement is profile-driven and reusable, not a South Plateau-specific exception;
- no generated legal conclusion is introduced beyond citation-bearing package/source evidence and
  validation gates.

## Non-Goals

- Do not mark `forest_plan_profile` optional for ready expansion slots.
- Do not remove South Plateau's declared `custer_gallatin` profile merely to make strict promotion
  pass.
- Do not treat a broad mention of "Forest Plan", "Land Management Plan", or "Custer Gallatin" as
  sufficient context by itself.
- Do not classify bibliographic/reference-list mentions as project location without a supported
  project-location signal.
- Do not add a new Region 1 forest profile or run broad source capture in this milestone.
- Do not stage ignored `source_library/` generated artifacts unless repository policy changes.

## Current Baseline

The current strict-expansion blocker is narrow and should stay narrow:

- review ID: `region1-expansion-south-plateau-landscape-treatment`;
- package path:
  `source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment`;
- source set: `source-set-ba8d0feae79501b8`;
- imported package: `26` official PDFs, `3,671` package chunks;
- applicability validation: `61` applicable, `331` non-applicable, `0` unresolved or
  `needs_adjudication`, `generated_rule_pack_ready=true`;
- generated rule pack: `61` generated rules;
- compliance review: `reviewer_ready=true`, `61` findings, `41` pass, `19` uncertain, `1` gap,
  `280` rule-claim links, `0` rule-claim gaps;
- review-scoped phase eval: `16/16`, `reviewer_ready=true`;
- strict expansion: expected failure on `forest_plan_reviewer_not_ready`.

The forest-plan artifacts show the actual blocker:

- `forest_plan_context_validation.json` passes schema, source-readiness not-applicable, area
  not-applicable, evidence-shape, and supporting-route checks, but fails
  `scope_status_resolved` with `scope_status="ambiguous"`;
- `forest_plan_context_summary.json` records `project_location_signal_count=2`,
  `unresolved_mention_count=10`, `supporting_plan_evidence_count=0`,
  `validation_passed=false`, and `reviewer_ready=false`;
- `forest_plan_context.json` records package signals for both `Hebgen Lake Ranger District` and a
  bibliographic/reference-list `Bozeman Ranger District` mention, so the next pass must separate
  project-location evidence from references before resolving scope.

## Relevant Surfaces

- `config/forest_plan_profiles.json`
- `config/promotion_suite_v1.json`
- `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/promotion_suite.py`
- `tests/test_forest_plan_resolver.py`
- `tests/test_compliance_review.py`
- `tests/test_promotion_suite.py`
- `docs/FOREST_PLAN_REVIEW_EVALUATOR_V1.md`
- `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`

## Sequence 0: Baseline And Failure Reproduction

Purpose: prove the current blocker and prevent the implementation pass from chasing broader
expansion or unrelated compliance-review behavior.

Actions:

1. Inspect `forest_plan_context.json`, `forest_plan_context_validation.json`,
   `forest_plan_context_summary.json`, `compliance_review.json`, South Plateau review-scoped
   `phase_eval_results.json`, and strict/non-strict promotion-suite results.
2. Add or update a regression fixture that captures the current shape:
   - package signals include `Hebgen Lake Ranger District`;
   - package signals also include a bibliographic/reference-list `Bozeman Ranger District` mention;
   - validation fails `scope_status_resolved`;
   - strict expansion fails with `forest_plan_reviewer_not_ready`.
3. Record exact baseline counts in the handoff before changing resolver logic.

Acceptance:

- The failing condition is reproduced without rewriting package artifacts.
- The fixture makes a future false pass visible if ambiguous forest-plan context is accidentally
  treated as reviewer-ready.
- Current V1 promotion remains green in the baseline.

Verification:

```bash
jq '.checks[] | select(.passed == false)' \
  source_library/reviews/region1-expansion-south-plateau-landscape-treatment/forest_plan_context_validation.json

jq '{scope_status, reviewer_ready, validation_passed, project_location_signal_count, unresolved_mention_count}' \
  source_library/reviews/region1-expansion-south-plateau-landscape-treatment/forest_plan_context_summary.json

PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_promotion_suite.py
git diff --check
```

Stop if the generated artifacts are missing, stale, or no longer show the documented
`scope_status="ambiguous"` blocker.

## Sequence 1: Location-Evidence Classification Contract

Purpose: make the resolver distinguish project-location signals from bibliographic or background
mentions using general evidence rules.

Actions:

1. Audit how the resolver currently assigns package evidence categories for forest unit, district,
   geographic area, management area, and overlays.
2. Add profile-driven evidence roles or scoring if needed so:
   - title/header/cover/project-description occurrences can support project location;
   - references, literature citations, and source bibliographies are weak/background unless paired
     with stronger project-location evidence;
   - ranger-district evidence can support a forest-profile candidate only through profile data,
     never through hard-coded project names.
3. Add focused tests for:
   - South Plateau-style `Hebgen Lake Ranger District, Custer Gallatin National Forest` header
     evidence as a strong Custer Gallatin location signal;
   - a reference-list `Bozeman Ranger District` mention as non-decisive background evidence;
   - selected-profile isolation so a district term cannot resolve an unrelated forest profile.

Acceptance:

- The resolver emits enough evidence metadata for reviewers to see why a mention did or did not
  count as project location.
- Bibliographic false positives do not resolve scope.
- Strong package-location evidence can select a profile only when the profile data supports that
  relationship.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop if resolving South Plateau requires a branch keyed to the South Plateau review ID, package
filename, or project number.

## Sequence 2: Profile-Driven Custer Gallatin Resolution

Purpose: resolve the South Plateau package to Custer Gallatin only if package and profile evidence
are strong enough, then make any remaining Custer-specific context requirements explicit.

Actions:

1. If the profile lacks a data-backed relationship needed by the resolver, add it to
   `config/forest_plan_profiles.json` with a source/evidence rationale, not hidden runtime logic.
2. Rerun the forest-plan resolver or compliance review against the existing South Plateau package
   cache using `--reuse-package-cache`.
3. Require the generated context to show:
   - `scope_status="custer_gallatin"`;
   - `validation_passed=true`;
   - `reviewer_ready=true`;
   - package evidence for the selected profile;
   - no unresolved higher-priority conflicting forest-unit signal.
4. If context resolves to Custer Gallatin but geography, management area, overlay, or supporting
   source routes remain unresolved, carry those as validation failures or reviewer-resolution items
   rather than marking the slot ready.

Acceptance:

- South Plateau either resolves to Custer Gallatin with reviewer-ready context, or the plan records
  the narrower blocker that prevents that result.
- The generated context summary explains the evidence path in package/source terms.
- The slot is not marked ready from a manifest edit alone.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment \
  --output-dir source_library \
  --rule-pack source_library/reviews/region1-expansion-south-plateau-landscape-treatment/applicability/generated_rule_pack.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id region1-expansion-south-plateau-landscape-treatment \
  --reuse-package-cache

jq '{scope_status, validation_passed, reviewer_ready, project_location_signal_count, unresolved_mention_count}' \
  source_library/reviews/region1-expansion-south-plateau-landscape-treatment/forest_plan_context_summary.json

PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_compliance_review.py
git diff --check
```

Stop if the package cannot be defensibly distinguished from generic Custer Gallatin plan references
or if source-library Custer Gallatin readiness has drifted.

## Sequence 3: Forest-Plan Component Gate And Review Output

Purpose: once Custer Gallatin context is reviewer-ready, ensure the compliance output includes the
right forest-plan component gate rather than relying on the earlier zero-row forest-plan matrix.

Actions:

1. Rerun South Plateau compliance review from the generated rule pack and existing package cache.
2. Inspect `forest_plan_component_findings.json`, `forest_plan_reviewer_resolution_queue.json`,
   `forest_plan_component_inventory_coverage.json`,
   `forest_plan_applicable_standard_coverage.json`, and the compliance matrix summary.
3. If component evaluation produces a reviewer-resolution queue, run the existing
   `forest-plan-component-adjudication-template` / `forest-plan-component-adjudication-eval` path
   before considering the expansion slot ready.
4. Update promotion-suite expected gate artifacts with exact South Plateau forest-plan counts only
   after the generated artifacts pass.

Acceptance:

- A resolved Custer Gallatin South Plateau review does not retain a misleading
  `matrix_forest_plan_row_count=0` readiness claim.
- Supported/partial/gap component findings carry both plan-source and package evidence, or remain
  visible reviewer-resolution items.
- Phase eval includes the required forest-plan component eval or component-adjudication phase when
  the component gate is required.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop if component evaluation would require inventing package support or treating true package
omissions as plan consistency.

## Sequence 4: Strict Expansion Promotion Closeout

Purpose: close the milestone by making strict expansion truthfully reflect South Plateau forest-plan
readiness.

Actions:

1. Update `config/promotion_suite_v1.json`:
   - if South Plateau is reviewer-ready, set the slot `ready=true`, remove the failure category,
     and record exact artifact/count signals;
   - if South Plateau is still blocked, keep `ready=false`, retain
     `forest_plan_reviewer_not_ready` or a narrower typed failure, and update `next_action`.
2. Rerun South Plateau review-scoped phase eval.
3. Rerun the promoted V1 review-scoped phase eval if the shared current-promotion artifact is
   overwritten.
4. Rerun strict and non-strict promotion suite, writing strict results to the explicit strict
   expansion result directory and rerunning non-strict last.
5. Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`,
   `docs/POST_V1_PROMOTION_SUITE.md`,
   `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md`,
   `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md`, and `docs/SESSION_HANDOFF.md`.

Acceptance:

- Non-strict promotion keeps `current_promotion_ready=true` and `promotion_ready=true`.
- Strict expansion either:
  - passes with `expansion_ready=true` and no expansion failure categories; or
  - fails only on the explicit South Plateau forest-plan blocker, with no current-promotion
    regression.
- Docs state the exact package set, artifact signals, verification commands, and residual risk.

Verification:

```bash
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
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_components.py tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/promotion_suite_v1.json /tmp/promotion_suite_v1.validated.json
git diff --check
```

## Completion Definition

This milestone is complete when South Plateau's declared forest-plan profile no longer creates an
ambiguous strict-expansion state. The acceptable final states are:

- `strict-expansion`: South Plateau resolves to reviewer-ready Custer Gallatin forest-plan context,
  all required generated review and promotion artifacts pass, and `expansion_ready=true`; or
- `typed-blocker`: South Plateau remains blocked, but the blocker is narrower than the current
  ambiguous context state and the next action is concrete enough for a follow-up milestone.

## Commit Policy

Commit each sequence as an atomic slice after verification passes. Stage only the intended code,
tests, docs, config, and small tracked fixtures. Do not stage ignored generated `source_library/`
artifacts or root-level manual East Crazies draft exports.

## Stop Conditions

- South Plateau resolution depends on project-specific runtime branching.
- Bibliographic or reference-list evidence is needed as the decisive project-location signal.
- Custer Gallatin context can resolve only by suppressing conflicting package evidence rather than
  classifying it.
- Component evaluation would require converting missing package evidence into support.
- Strict expansion can pass while `forest_plan_context_summary.json` still records ambiguous,
  failed, or not reviewer-ready forest-plan context.
- Closing the milestone would require live network/source capture, a new forest profile, or a full
  corpus rebuild outside this scope.
