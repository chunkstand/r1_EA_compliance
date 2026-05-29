# Beaverhead-Deerlodge South Tobacco Roots Example Package Milestone Plan

Date: 2026-05-29
Status: Reduced locally through Milestone 4 registry and coverage promotion; Beaverhead-owned
promotion slots pass, with only inherited ECID source-delta component-coverage drift keeping the
standalone component-coverage aggregate red.
Plan class: implementation
High-risk implementation: yes
Owner context: follow-on to `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Intent lock: `review_id="region1-example-beaverhead-deerlodge-south-tobacco-roots-63754"` is only
for Beaverhead-Deerlodge National Forest South Tobacco Roots package work. It is not a generic
Region 1 example and not reusable for Custer Gallatin, HLC, Bitterroot, Lolo, or Flathead.

## Purpose

Keep the South Tobacco Roots Vegetation Management Project as a governed Beaverhead-Deerlodge
forest-specific example lane while preventing cross-forest reuse or master-register contamination.

Package identity:

- project page: `https://www.fs.usda.gov/r01/beaverhead-deerlodge/projects/63754`
- Pinyon/Box folder: `https://usfs-public.app.box.com/v/PinyonPublic/folder/199281418011`
- project ID/title: `63754`, `South Tobacco Roots Vegetation Management Project`
- selected folder: `Final EA and FONSI`
- forest unit: `beaverhead-deerlodge-nf`
- example/coverage slot: `bdnf-south-tobacco-roots-forest-specific`

## Intent Hierarchy

- Invariant: South Tobacco Roots stays parallel to `Document_Register_Master`; it is package
  replay evidence, not master-register source capture.
- Optimization target: keep Milestone 3 reviewer-ready evidence replayable while leaving registry
  state truthful.
- Acceptable tradeoff: close Milestone 4 as `reduced` if only the inherited ECID component-coverage
  slot remains red and the Beaverhead slot passes.
- Non-negotiables: do not weaken tests, evals, adjudication gates, registry thresholds, or
  component-coverage requirements to make promotion pass.

## Current Evidence

- Registry state: `beaverhead-deerlodge-nf` is now
  `real_package_examples_available` in
  `config/forest_specific_example_package_registry_v1.json`, with
  `primary_example_id="bdnf-south-tobacco-roots-forest-specific"`.
- Promotion slots exist in `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`, and registry
  `review_examples[]` for the frozen review ID.
- Local ignored intake under
  `source_library/reviews/_intake/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754/`
  has `16` files, `176,594,060` bytes, and `failure_count=0`.
- `ea-review` passes with `16/16` extracted files, `1,382` package chunks, and
  `validation_passed=true`.
- Review-local Beaverhead component inventory has `90` components and `89` standards.
- `forest-plan-resolve` reports `scope_status="beaverhead_deerlodge_nf"`,
  `validation_passed=true`, `geographic_area_count=2`, `management_area_count=3`,
  `overlay_count=2`, and `unresolved_mention_count=0`.
- Component adjudication resolves `60/60` reviewer-resolution items as
  `evidence_linking_miss` with `0` pending items.
- Applicability adjudication resolves `3/3` trigger conflicts; validation reports `52`
  applicable authorities, `104` not-applicable authorities, and `0` unresolved authorities.
- Generated rule-pack validation passes with `52` rules; `compliance-review`, V1 eval, component
  eval, and review `phase-eval` pass. After Milestone 4 promotion, `phase-eval` reports `28/28`,
  `blockers=[]`, `declared_review_contract=true`, and
  `contract_backed_promotion_ready=true`.

## Goal

Promote the resolved Milestone 3 replay checkpoint into governed Beaverhead-Deerlodge registry,
real-package coverage, and component-coverage surfaces while preserving package identity and
parallel-to-master boundaries.

## Non-Goals

- Do not add South Tobacco Roots rows or files to `Document_Register_Master`.
- Do not promote Beaverhead-Deerlodge in queue ledger or `Document_Register_Master`.
- Do not overwrite shared f70 component inventory; keep package-specific component evidence
  review-local unless a separate milestone owns a shared update.
- Do not stage ignored `source_library/` package bytes or generated review outputs.

## Scope

- In scope: packet identity, replay context, tracked eval/adjudication contracts, Beaverhead
  profile/resolver guards, docs routing, registry promotion, real-package coverage promotion, and
  component-coverage slot promotion.
- Out of scope: unrelated Beaverhead projects, workbook source-register promotion, global
  component-inventory promotion, and non-Beaverhead aggregate blockers.

## Owner Surfaces And Placement

- packet: `docs/BEAVERHEAD_DEERLODGE_SOUTH_TOBACCO_ROOTS_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- replay context:
  `config/replay_contexts/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754.json`
- contracts:
  `config/v1_beaverhead_deerlodge_south_tobacco_roots_real_ea_eval.json`,
  `config/forest_plan_component_evals/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754.json`,
  `config/applicability_adjudications/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754.json`,
  `config/forest_plan_component_adjudications/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754.json`
- profile/resolver: `config/forest_plan_profiles.json`,
  `src/usfs_r1_ea_sources/forest_plan_resolver_location.py`
- promotion manifests:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_specific_example_package_registry_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- docs: `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, umbrella packet

## Weak-Point Prevention

| Weak point | Owner surface | Prevention gate | Fail threshold |
| --- | --- | --- | --- |
| URL-only promotion | Registry and real-package coverage manifests | V1 eval, component eval/adjudication, compliance review, phase eval, aggregate evals | Any Beaverhead primary example or required slot appears before matching reviewer-ready artifacts |
| Cross-forest scope | Resolver profile code and fixtures | Resolver regression for HLC comparison/background text | Resolver leaves `beaverhead_deerlodge_nf` or treats comparison text as project scope |
| Component scope mistaken for compliance closure | Component adjudication and component eval contracts | Component adjudication eval plus component eval | Pending adjudication, applicable-standard miss, or reviewer-ready false state remains |
| Shared master contamination | Workbook, queue ledger, downloader/catalog docs | Workbook/queue audit before source-register edits | Package docs become master-promotion rows without a governed workbook packet |
| Aggregate false green/red | Component-coverage manifest and result artifact | Slot-level component-coverage readback | Beaverhead slot missing/stale/mismatched, or ECID inherited failure is reported as Beaverhead-owned |

## Milestone Sequence

### Milestone 0 - Open Packet And Freeze Boundary

Outcome label: `resolved`

Freeze review ID, forest ID, official project/Box URLs, and no-promotion status. Stop if another
tracked packet owns the same review ID.

### Milestone 1 - Local Package Authority Intake

Outcome label: `resolved`

Inventory/download the official Box package, preserve hashes and byte counts, and run `ea-review`.
Local result: `16` files, `176,594,060` bytes, zero download failures, and package review green.

### Milestone 2 - Forest-Plan Resolver Preflight

Outcome label: `reduced`

Build review-local Beaverhead component inventory, add narrow South Tobacco Root profile aliases,
guard HLC comparison text, and run `forest-plan-resolve`. This checkpoint was reduced because
component adjudication still remained, then superseded by Milestone 3.

### Milestone 3 - Component Adjudication And Reviewer Stack Replay

Outcome label: `resolved`

Track component and applicability adjudications, rerun forest-plan resolution, generated rule-pack
validation, compliance review, V1 eval, component eval, and review `phase-eval`. Local result:
all review-scope gates pass; registry and coverage remain unpromoted.

### Milestone 4 - Registry And Coverage Promotion

Outcome label: `reduced`

Beaverhead promotion and all Beaverhead-owned aggregate slots pass. The standalone
component-coverage aggregate remains red solely on the inherited ECID source-delta slot.

Preconditions:

- Milestone 3 still passes with `reviewer_ready=true` and `phase-eval` `blockers=[]`.
- Local package inventory still matches `16` files and `176,594,060` bytes.

Applied mutations:

- Add real-package slot `bdnf-south-tobacco-roots-forest-specific` for the frozen review ID,
  `forest_specific_reviewer_ready`, expected `reviewer_ready`, official authority URLs, replay
  context, and `v1_beaverhead_deerlodge_south_tobacco_roots_real_ea_eval.json`.
- Add registry `review_examples[]` entry and set only the Beaverhead routing row to
  `real_package_examples_available` with primary example
  `bdnf-south-tobacco-roots-forest-specific`.
- Add component-coverage slot for the frozen review ID with
  `expected_source_set_id="source-set-f70ea11e04ae3d53"` and eval file
  `forest_plan_component_evals/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754.json`.
- Update thresholds coherently: real-package required/reviewer-ready slots `6 -> 7`; real-package
  distinct forests `5 -> 6`; distinct package-style tags `7 -> 8`; registry
  review/reviewer-ready examples `6 -> 7`; governed example forests `5 -> 6`; guidance-only max
  `5 -> 4`; component required reviews `7 -> 8`; component distinct forests `5 -> 6`.

## Verification Gates

Milestone 3 replay gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id region1-example-beaverhead-deerlodge-south-tobacco-roots-63754 --adjudication-file config/forest_plan_component_adjudications/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754.json
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-example-beaverhead-deerlodge-south-tobacco-roots-63754 --eval-file config/v1_beaverhead_deerlodge_south_tobacco_roots_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id region1-example-beaverhead-deerlodge-south-tobacco-roots-63754 --eval-file config/forest_plan_component_evals/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-beaverhead-deerlodge-south-tobacco-roots-63754
```

Milestone 4 promotion gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-beaverhead-deerlodge-south-tobacco-roots-63754
```

Plan/commit gates:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/BEAVERHEAD_DEERLODGE_SOUTH_TOBACCO_ROOTS_EXAMPLE_PACKAGE_MILESTONE_PLAN.md --strict
PYTHONPATH=src uv run --extra dev pytest tests/test_beaverhead_south_tobacco_contracts.py tests/test_real_package_review_coverage_eval.py tests/test_forest_specific_example_package_eval.py tests/test_forest_plan_component_eval_coverage.py
git diff --check
```

## Acceptance Criteria

- Replay context binds the frozen review ID to `beaverhead-deerlodge-nf`,
  `source-set-f70ea11e04ae3d53`, and `source_library/catalog`.
- Package authority remains `16` files, `176,594,060` expected and actual bytes, and zero failures.
- Resolver, component adjudication, applicability adjudication, generated rule pack, compliance
  review, V1 eval, component eval, and review `phase-eval` pass for the frozen review ID.
- Beaverhead now routes as `real_package_examples_available` with primary example
  `bdnf-south-tobacco-roots-forest-specific`.
- Milestone 4 adds exactly one Beaverhead real-package slot, registry primary example, and
  component-coverage slot with no cross-forest reuse.

## Documentation And Handoff

- Milestone 4 closeout docs must reflect Beaverhead promotion:
  `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and umbrella packet.
- Cite generated `source_library/` counts and paths only; do not stage generated bytes.

## Commit Closeout

Complete-after-commit. Each milestone slice must be verified, docs-aligned, and committed locally
before it is complete. Stage only the scoped Beaverhead files and push only on explicit request.

## Stop Conditions

- Package authority counts drift or package download/hash evidence fails.
- Scope resolves outside `beaverhead-deerlodge-nf` or becomes ambiguous.
- Any required gate fails and fixing it would weaken tests, evals, thresholds, or adjudication.
- Promotion needs broader source-register, shared-inventory, or non-Beaverhead aggregate work.
- Milestone 4 threshold math hides a missing or failing Beaverhead slot.

## Residual Risks And Next Routing

Next route is a new forest-specific example packet or a separate inherited ECID source-delta
component-coverage repair. The known non-Beaverhead component-coverage blocker remains inherited
ECID source-delta drift; it is not Beaverhead-owned.

## Closeout Outcome Record

- Milestone 3 outcome: `resolved` locally and committed before this compact-plan revision.
- Pre-Milestone 4 compact-plan revision outcome: docs-only plan compression; no registry,
  coverage, or generated evidence state changed at that historical checkpoint.
- Milestone 4 outcome: `reduced` locally because Beaverhead registry, real-package coverage,
  component-coverage slot, and review-scope `phase-eval` promotion are green, while the standalone
  component-coverage aggregate remains red solely on inherited ECID source-delta drift.
- Milestone 4 verification: real-package coverage `7/7` covered and reviewer-ready slots across
  `6` forests and `8` package-style tags; forest-specific registry eval passes with `10/10`
  forests covered, `7` reviewer-ready examples, `6` governed example forests, and `4`
  profile-guidance-only forests; component coverage reports `7/8` covered reviews with the
  Beaverhead slot passing and only `ecid-source-delta-replay` red on `result_not_passed` and
  `result_source_set_id_mismatch`; Beaverhead `phase-eval` passes `28/28` with `blockers=[]`,
  `declared_review_contract=true`, and `contract_backed_promotion_ready=true`.
- Milestone 4 implementation commit: `924f60e`
