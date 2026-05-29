# Bitterroot Front Example Package Milestone Plan

Date: 2026-05-29
Status: Active packet (`Milestone 3 reviewer-stack replay next; Milestone 2 resolver/adjudication closed locally`)
Owner context: standalone follow-on from `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`

## Purpose

Open the governed Bitterroot National Forest example-package lane around the
user-selected Bitterroot Front EA package without contaminating
`Document_Register_Master` or claiming reviewer-ready status before the
deterministic review gates pass.

Selected package authority:

- project page: `https://www.fs.usda.gov/r01/bitterroot/projects/57341`
- project title: `Bitterroot Front`
- project ID: `57341`
- public Pinyon/Box folder:
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158226983588`
- Box root folder label: `Bitterroot Front (57341)`
- forest: `bitterroot-nf`
- ranger district: `Stevensville Ranger District`
- expected analysis type: `Environmental Assessment`
- project status: `Completed`
- decision signed date: `2026-05-11`
- frozen review ID: `region1-example-bitterroot-front-57341`
- queue boundary source ID: `FOR-007`

## Intent Lock

Bitterroot Front is a Bitterroot National Forest example candidate. It is not a
generic Region 1 example, not a substitute for Flathead, Lolo, Custer Gallatin,
or Helena-Lewis and Clark packages, and not evidence that any other forest has
a governed real-package example.

The planned governed identity is:

- `example_id="bitterroot-front-forest-specific"`
- `review_id="region1-example-bitterroot-front-57341"`
- `forest_unit_id="bitterroot-nf"`
- `applicable_forest_unit_ids=["bitterroot-nf"]`
- `coverage_slot_id="bitterroot-front-forest-specific"`
- `coverage_class_id="forest_specific_reviewer_ready"`
- `queue_lineage_source_ids=["FOR-007"]`

Bitterroot must remain `profile_eval_guidance_only` in
`config/forest_specific_example_package_registry_v1.json` until Bitterroot
Front passes package authority, replay context, forest-plan
component/adjudication, compliance, V1 eval, phase eval, and review-scope
promotion gates. `FOR-007` may route to this packet as a planned
forest-specific example boundary before promotion, but it must not emit rows
into `Document_Register_Master`.

## Current Evidence

- Live Forest Service project page readback on 2026-05-29 identifies
  Bitterroot Front as project `57341`, `Completed`, with expected analysis type
  `Environmental Assessment`, forest `Bitterroot National Forest`, district
  `Stevensville Ranger District`, and decision signed date `2026-05-11`.
- The official project page links to Pinyon/Box folder
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158226983588`.
- Live Box readback identifies the root folder as `Bitterroot Front (57341)`
  under `Bitterroot National Forest (110103)` >
  `Stevensville Ranger District (11010301)`.
- The live Box root currently exposes five top-level package folders:
  `Final EA` (`38` files), `Decision Notice` (`7` files), `Draft EA`
  (`68` files), `Scoping` (`12` files), and `Pre-Scoping` (`7` files).
- `config/source_register_queue_resolution_ledger_v1.json` now routes
  `FOR-007` (`Bitterroot Front Project`) to this packet with
  `planned_disposition="forest_specific_example_package"` and
  `resolution_status="planned"` while preserving the workbook-matching source
  row identity.
- `config/forest_specific_example_package_registry_v1.json` still routes
  `bitterroot-nf` as `profile_eval_guidance_only`; the registry row names
  `FOR-007` only as the open queue boundary, not as reviewer-ready proof.
- Local ignored package authority now exists under
  `source_library/reviews/_intake/region1-example-bitterroot-front-57341/`.
  `box_inventory.json` records `41` folders, `132` visible files, and
  `632,912,037` expected bytes. `box_import_manifest.json` records `132`
  downloaded files, `632,912,037` actual bytes, and `failure_count=0`.
- The tracked replay context
  `config/replay_contexts/region1-example-bitterroot-front-57341.json` points
  to current source set `source-set-f70ea11e04ae3d53`, the repo-root current
  catalog, the local intake package, and the official project/Box authority
  paths.
- `ea-review` passed on the full package with `132/132` files extracted,
  `5,463` package chunks, `package_failed_count=0`,
  `validation_passed=true`, and `reviewer_ready=true`.
- Existing governed examples remain South Otter and East Crazy for Custer
  Gallatin, West Reservoir for Flathead, Tyler's Kitchen for Lolo, and Bonanza
  for Helena-Lewis and Clark.
- Milestone 0 verification passed: plan lint, focused queue/registry tests
  (`20/20`), source-register queue audit (`validation_passed=true`),
  `forest-specific-example-package-eval` (`passed=true`), and
  `git diff --check`.
- Milestone 1 verification passed: Box inventory/download byte and hash
  manifest completed with zero failures, replay context JSON validated, and
  `ea-review` passed on `source-set-f70ea11e04ae3d53`.
- Milestone 2 forest-plan resolver preflight is resolved locally on
  `source-set-f70ea11e04ae3d53`: the `forest-plan-resolve` run with
  `--forest-unit-id bitterroot-nf` writes sidecars with
  `scope_status="bitterroot_nf"`,
  `project_location_signal_count=1`, `management_area_count=4`,
  `overlay_count=2`, and `unresolved_mention_count=0`. Context validation now
  passes because the f70 source-record blocker for
  `R1PLAN-bitterroot-nf-12` and `R1PLAN-bitterroot-nf-13` is closed locally.
- The source-record closure is local ignored evidence only. The f70 catalog
  gate and repo-root current catalog now carry `717` source rows, `705`
  artifacts, and `9` supplemental overlay rows. The two Bitterroot BA/BO rows
  are provenanced from the archived source-delta gate
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/`.
  `source-record-identity-gate` passes for both IDs, extraction/retrieval pass
  with `717` catalog sources and `111,233` chunks, and the retrieval index now
  has `115` chunks for `R1PLAN-bitterroot-nf-12` and `136` chunks for
  `R1PLAN-bitterroot-nf-13`.
- The f70 component-inventory blocker is closed locally. The tracked Region 1
  component-inventory build manifest now has a
  `bitterroot_replay_compatible` source-set reference for
  `source-set-f70ea11e04ae3d53`, and the review-local manifest-driven build
  under ignored
  `source_library/reviews/region1-example-bitterroot-front-57341/component_inventory_build/`
  uses `FOR-005` and `FOR-006` as component-bearing sources. It passes with
  `component_count=23`, `standard_count=3`, `coverage_passed=true`,
  `blocked_forest_unit_ids=[]`, and `6` non-blocking inventory quality issues.
  This is component-inventory proof only, not registry, coverage, or
  reviewer-ready promotion proof.
- Tracked component adjudication is now closed at
  `config/forest_plan_component_adjudications/region1-example-bitterroot-front-57341.json`.
  `forest-plan-component-adjudication-eval` passes with `20/20`
  reviewer-resolution items resolved, `0` pending items,
  `12` applicability false positives, `8` evidence-linking misses, and
  `0` true EA omissions. A rerun `forest-plan-resolve` reports
  `component_adjudication.reviewer_ready=true`,
  `needs_reviewer_resolution=false`, `validation_passed=true`, and
  `reviewer_ready=true`.
- Raw applicable-standard coverage remains red with `3` applicable standards
  and `1` applied standard, but the two standard gaps are classified in the
  adjudication replay: the A-P cabin maintenance/rehabilitation standard is an
  applicability false positive for this package and `FOR-006-FW-STD-VEG-01` is
  an evidence-linking miss against package old-growth evidence. This raw red
  coverage is retained as Milestone 3 reviewer-stack/component-eval diagnostic
  evidence, not as a remaining Milestone 2 adjudication blocker.

## Goal

Create and close a governed Bitterroot Front example package lane as the
Bitterroot primary example only after package authority, review artifacts, eval
contracts, and aggregate gates are all present and green.

## Non-Goals

- Do not add Bitterroot Front package files or project-specific rows to
  `Document_Register_Master`.
- Do not promote Bitterroot to `real_package_examples_available` before local
  package intake, replay context, `v1-ea-eval`, forest-plan component eval, and
  review `phase-eval` pass.
- Do not ratchet real-package, forest-specific, or component-coverage aggregate
  thresholds in Milestone 0.
- Do not treat a project page or Box folder listing as row-level source
  capture evidence for the shared master.
- Do not stage ignored `source_library/` evidence unless repository policy
  changes explicitly.

## Scope

- Bitterroot Front package-boundary and review identity
- queue-boundary truth for `FOR-007`
- packet routing and current-state docs
- package-authority intake planning
- future tracked contracts for replay, review eval, applicability
  adjudication, forest-plan component eval, and aggregate coverage
- registry and coverage promotion only after review-readiness gates pass

## Out Of Scope

- unrelated Bitterroot projects
- unrelated profile-only forests
- full-canonical source capture or catalog rebuilds
- broad reviewer-engine refactors
- manual legal conclusions or responsible-official decisions
- promotion of `FOR-004` or Bitterroot forest-plan planning page rows

## Owner Surfaces

- packet:
  `docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- queue routing:
  `config/source_register_queue_resolution_ledger_v1.json`
- forest-specific umbrella:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- forest-specific registry:
  `config/forest_specific_example_package_registry_v1.json`
- future replay context:
  `config/replay_contexts/region1-example-bitterroot-front-57341.json`
- future review eval contract:
  `config/v1_bitterroot_front_real_ea_eval.json`
- future forest-plan component eval contract:
  `config/forest_plan_component_evals/region1-example-bitterroot-front-57341.json`
- future applicability adjudication:
  `config/applicability_adjudications/region1-example-bitterroot-front-57341.json`
- future forest-plan component adjudication:
  `config/forest_plan_component_adjudications/region1-example-bitterroot-front-57341.json`
- aggregate manifests after promotion is allowed:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_specific_example_package_registry_v1.json`, and
  `config/forest_plan_component_eval_coverage_v1.json`
- local ignored intake:
  `source_library/reviews/_intake/region1-example-bitterroot-front-57341/`
- local ignored review outputs:
  `source_library/reviews/region1-example-bitterroot-front-57341/`
- docs:
  `docs/AGENT_START_HERE.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`, and
  `README.md` if start-here routing changes materially
- tests:
  `tests/test_source_register_queue_resolution.py`,
  `tests/test_forest_specific_example_package_registry.py`,
  `tests/test_forest_specific_example_package_eval.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_forest_plan_component_eval_coverage.py`, and
  `tests/test_cli_eval.py`

## Placement Rules

- Freeze the review slug before intake:
  `region1-example-bitterroot-front-57341`.
- Keep the example and coverage identifiers Bitterroot scoped:
  `bitterroot-front-forest-specific`.
- Keep `FOR-007` as a queue-boundary lineage row for the example package; do
  not resolve it as a master direct-file promotion.
- Treat the Pinyon/Box folder `158226983588` as the selected root package
  boundary until a package inventory proves a narrower official final package
  path is required.
- Preserve the full root as package-authority evidence even if replay later
  narrows to `Final EA` and `Decision Notice`.
- Keep package bytes and generated review outputs under ignored
  `source_library/` paths.
- Keep tracked review contracts under `config/` and docs/handoff truth updated
  before each milestone commit.

## Weak-Point Prevention Contract

### Weak Point 1

Weak point forecast: Bitterroot Front is ingested as shared master input.

- Owner surface: `config/source_register_queue_resolution_ledger_v1.json` and
  active workbook queue row `FOR-007`
- Prevention gate:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_queue_resolution.py tests/test_forest_specific_example_package_registry.py`
- Fail threshold: `FOR-007` returns to
  `planned_disposition="promote_direct_file"` or any Bitterroot Front package
  row is added to `Document_Register_Master` without a separate governed
  source-register promotion packet
- Controlled violation: focused registry and queue tests fail if `FOR-007`
  loses its packet reference or is presented as a resolved direct-file
  promotion
- Future-Codex misuse scenario: a future session sees the official project
  page and converts the folder into master rows; this packet keeps it parallel
  until a separate source-register packet proves otherwise

### Weak Point 2

Weak point forecast: an agent claims Bitterroot reviewer-ready status from URL
or folder inventory alone.

- Owner surface:
  `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`, and
  `config/forest_plan_component_eval_coverage_v1.json`
- Prevention gate:
  `forest-specific-example-package-eval`, `real-package-review-coverage-eval`,
  review `phase-eval`, V1 eval, and component eval
- Fail threshold: Bitterroot row leaves `profile_eval_guidance_only`, or a
  Bitterroot slot becomes required reviewer-ready coverage, before package
  authority and review gates pass
- Controlled violation: registry tests must fail if Bitterroot has a primary
  example while no matching real-package coverage slot and eval contract exist
- Future-Codex misuse scenario: a future session adds a registry row after
  downloading files but before deterministic review; aggregate gates must keep
  that false green out

### Weak Point 3

Weak point forecast: the package authority drops analysis, scoping, or
supporting record families and keeps only decision-core PDFs.

- Owner surface:
  `source_library/reviews/_intake/region1-example-bitterroot-front-57341/`
  and future replay context
- Prevention gate: package inventory, import manifest, and `ea-review`
  package validation
- Fail threshold: local package authority lacks `Final EA`, `Decision Notice`,
  `Draft EA`, `Scoping`, or `Pre-Scoping`, unless a milestone documents and
  tests a narrower official replay path
- Controlled violation: remove one required root folder from the intake
  manifest and require package-authority validation to fail
- Future-Codex misuse scenario: a future session reviews only final decision
  PDFs and misses specialist/supporting material; the package-authority gate
  must make that visible

### Weak Point 4

Weak point forecast: Bitterroot forest-plan scope is mistaken for Forest Plan
compliance readiness.

- Owner surface: future `forest_plan_context_summary.json`, component
  adjudication, and component eval contract
- Prevention gate: `forest-plan-resolve`, component adjudication eval, and
  `forest-plan-component-eval`
- Fail threshold: unresolved Bitterroot component queue items, missing source
  records, stale source set, or `reviewer_ready=false`
- Controlled violation: run `forest-plan-resolve` before component
  adjudication and preserve the typed blocker rather than weakening validation
- Future-Codex misuse scenario: a future session sees the project is in
  Bitterroot NF and promotes it without component proof; this packet separates
  scope resolution from reviewer-ready Forest Plan compliance

## Milestone Sequence

### Milestone 0 - Open Packet And Freeze Boundary

Outcome label: `resolved` when the packet exists, `FOR-007` is routed to this
packet as a planned forest-specific example boundary, and durable routing docs
name Bitterroot Front as the active candidate without registry promotion.

1. Verify the official project page and Box root metadata.
2. Freeze `review_id="region1-example-bitterroot-front-57341"` and
   `example_id="bitterroot-front-forest-specific"`.
3. Reroute `FOR-007` from generic direct-file promotion to planned
   `forest_specific_example_package` in the queue ledger.
4. Keep `bitterroot-nf` as `profile_eval_guidance_only` in the registry while
   recording `FOR-007` as the open queue boundary.
5. Update routing docs and handoff surfaces.
6. Verify with focused tests, plan lint, and `git diff --check`.

### Milestone 1 - Local Package Authority Intake

Outcome label: `resolved` locally. The official Box root is inventoried,
downloaded, hashed, and validated with zero missing visible files.

1. Inventory the official Box root and record folder tree, file names, sizes,
   Box IDs, source folder URLs, and root path lineage.
2. Download visible package documents while preserving folder structure.
3. Hash every local file and record expected versus actual byte counts.
4. Add the tracked replay context only after local package authority exists.
5. Build the first package cache through `ea-review`.
6. Stop as `reduced` if any official documents cannot be inventoried,
   downloaded, or traced to the official root.

Closeout evidence:

- local ignored intake:
  `source_library/reviews/_intake/region1-example-bitterroot-front-57341/`
- tracked replay context:
  `config/replay_contexts/region1-example-bitterroot-front-57341.json`
- package authority manifest:
  `document_count=132`, `folder_count=41`, `failure_count=0`,
  `actual_total_byte_size=632,912,037`
- base review cache:
  `package_file_count=132`, `package_extracted_count=132`,
  `package_chunk_count=5,463`, `package_failed_count=0`,
  `reviewer_ready=true`, `validation_passed=true`
- next route:
  Milestone 2 forest-plan resolver preflight; do not promote Bitterroot Front
  to registry or coverage manifests before Milestones 2-4 pass.

### Milestone 2 - Forest-Plan Resolver Preflight

Outcome label: `resolved` if Bitterroot scope, source-record readiness,
component inventory, component adjudication, and resolver validation pass;
`reduced` if a named source-record, component, or adjudication blocker remains.

1. Use the current f70 catalog and Bitterroot forest-plan profile.
2. Run `forest-plan-resolve` with `--forest-unit-id bitterroot-nf`.
3. Preserve blockers for missing Bitterroot source records or unresolved
   component queue items.
4. Do not change registry or coverage manifests in this milestone.

Closeout evidence:

- outcome:
  `resolved locally`
- resolver:
  `scope_status="bitterroot_nf"`, `project_location_signal_count=1`,
  `management_area_count=4`, `overlay_count=2`,
  `unresolved_mention_count=0`
- source-record closure:
  `R1PLAN-bitterroot-nf-12` and `R1PLAN-bitterroot-nf-13` now resolve through
  the local f70 catalog/retrieval overlay. `source-record-identity-gate` passes
  for both IDs, context validation has `blocking_missing_source_record_ids=[]`,
  and the retrieval index has `115` and `136` chunks for the two records
  respectively.
- component-inventory closure:
  tracked manifest reference `bitterroot_replay_compatible` permits the
  Bitterroot component-inventory row on `source-set-f70ea11e04ae3d53`; the
  review-local manifest-driven build under
  `source_library/reviews/region1-example-bitterroot-front-57341/component_inventory_build/`
  uses `FOR-005` and `FOR-006`, emits `component_count=23`,
  `standard_count=3`, `coverage_passed=true`, and
  `blocked_forest_unit_ids=[]`
- adjudication and applicable-standard classification:
  tracked adjudication
  `config/forest_plan_component_adjudications/region1-example-bitterroot-front-57341.json`
  passes local eval with `20/20` reviewer-resolution items resolved,
  `0` pending items, `12` applicability false positives,
  `8` evidence-linking misses, and `0` true EA omissions. Raw
  applicable-standard coverage remains red with `3` applicable standards,
  `1` applied standard, and two standard gaps, but those gaps are now
  adjudicated as one applicability false positive and one evidence-linking
  miss.
- resolver validation:
  rerun `forest-plan-resolve` reports
  `component_adjudication.reviewer_ready=true`,
  `needs_reviewer_resolution=false`, `validation_passed=true`, and
  `reviewer_ready=true`
- promotion boundary:
  no registry or coverage manifest was changed

### Milestone 3 - Reviewer Stack Replay

Outcome label: `resolved` if applicability, generated rule pack, compliance
review, V1 eval, component eval, and review `phase-eval` all pass for
`region1-example-bitterroot-front-57341`; `reduced` if a named applicability,
component, compliance, or eval blocker remains.

1. Resolve deterministic applicability and component adjudication only through
   tracked config files.
2. Run applicability, generated rule-pack, compliance review, V1 eval,
   forest-plan component eval, and review `phase-eval`.
3. Add tracked eval/adjudication contracts only when generated evidence exists
   and passes.
4. Preserve generated `source_library/` evidence as ignored local artifacts
   unless repo policy changes.

### Milestone 4 - Registry And Coverage Promotion

Outcome label: `resolved` for Bitterroot promotion only after review-scope and
aggregate gates pass. If an unrelated inherited aggregate blocker remains,
mark that blocker as separate and do not route it back into Bitterroot Front.

1. Add Bitterroot Front to `config/v1_real_package_review_coverage_v1.json`.
2. Add Bitterroot Front as the Bitterroot primary example in
   `config/forest_specific_example_package_registry_v1.json`.
3. Add Bitterroot Front to component-eval coverage only after component eval
   passes.
4. Rerun real-package coverage eval, forest-specific example-package eval,
   component-coverage eval, and review `phase-eval`.
5. Resolve `FOR-007` as `forest_specific_example_package` only after the
   registry/coverage promotion gates pass.

## Required Implementation Artifacts

- Milestone 0:
  `docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `config/source_register_queue_resolution_ledger_v1.json`, routing docs, and
  focused tests.
- Milestone 1:
  ignored package intake under
  `source_library/reviews/_intake/region1-example-bitterroot-front-57341/`,
  `box_inventory.json`, `box_import_manifest.json`, and replay context.
- Milestone 2:
  forest-plan resolver summaries, validation sidecars, the replay-compatible
  Bitterroot component-inventory manifest reference, review-local component
  inventory evidence under ignored `source_library/`, and any tracked
  component adjudication needed to make remaining blockers explicit.
- Milestone 3:
  tracked V1 eval, applicability adjudication, component eval, generated rule
  pack validation, compliance matrix artifacts, and phase-eval output.
- Milestone 4:
  registry, real-package coverage, component coverage, docs, tests, and
  aggregate eval outputs aligned to the promotion truth.

## Required Documentation And Handoff Updates

Each milestone closeout must update affected docs before commit:

- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/AGENT_START_HERE.md`
- `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- this plan's current evidence and status
- `README.md` only if start-here routing or stable repo contract text changes

The handoff must record the completed milestone, verification commands, commit
hash, residual risks, generated artifact boundaries, and next milestone route.

## Required Verification Gates

Opening/routing slice:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md
PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_queue_resolution.py tests/test_forest_specific_example_package_registry.py
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
git diff --check
```

Package intake and replay slices, scaled to touched surfaces:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review --output-dir source_library --review-id region1-example-bitterroot-front-57341
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id region1-example-bitterroot-front-57341 --adjudication-file config/forest_plan_component_adjudications/region1-example-bitterroot-front-57341.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/_intake/region1-example-bitterroot-front-57341 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-bitterroot-front-57341 --forest-unit-id bitterroot-nf --forest-plan-component-inventory-path source_library/reviews/region1-example-bitterroot-front-57341/component_inventory_build/derived/source-set-f70ea11e04ae3d53/forest_plan_components/component_inventory.json --reuse-package-cache --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-example-bitterroot-front-57341 --eval-file config/v1_bitterroot_front_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id region1-example-bitterroot-front-57341 --eval-file config/forest_plan_component_evals/region1-example-bitterroot-front-57341.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-bitterroot-front-57341
```

Promotion slice:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_real_package_review_coverage_eval.py tests/test_forest_specific_example_package_eval.py tests/test_forest_plan_component_eval_coverage.py tests/test_forest_specific_example_package_registry.py
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
PYTHONPATH=src python -m compileall src
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

The standalone `forest-plan-component-eval-coverage` command may still fail on
an inherited non-Bitterroot slot. If that happens, the Bitterroot closeout must
prove the Bitterroot slot is present, covered, source-set aligned, and passing,
then route the unrelated aggregate blocker to its own packet.

## Acceptance Criteria

- `FOR-007` is no longer a generic direct-file promotion candidate and instead
  points to this packet as a planned forest-specific example boundary.
- `bitterroot-nf` remains `profile_eval_guidance_only` until reviewer-stack
  gates pass.
- No Bitterroot Front package files or project-specific rows are added to
  `Document_Register_Master`.
- Future promotion requires matching review ID, example ID, coverage slot,
  forest unit ID, source set ID, replay context, V1 eval, component eval, and
  phase-eval evidence.
- Focused tests reject queue, registry, and agent-routing drift.
- Docs and handoff surfaces identify this packet as the active Bitterroot
  follow-on and HLC Bonanza as the latest resolved example packet.

## Stop Conditions

- Stop if the only way to proceed is to add package rows to
  `Document_Register_Master`.
- Stop if the Box root cannot be inventoried or downloaded with traceable file
  identity.
- Stop if package replay requires weakening reviewer, forest-plan, or
  compliance validation.
- Stop if Bitterroot promotion would require changing shared thresholds before
  review evidence exists.
- Stop if unrelated dirty worktree changes cannot be separated from the
  milestone slice.

## Local Commit Closeout Policy

`complete-after-commit` rule: a milestone is not complete until verification
passes, durable docs and handoff updates land, and the local atomic commit
exists. Stage only the verified milestone slice. Leave unrelated dirty or
untracked files alone. Generated `source_library/` evidence remains ignored
unless repository policy changes.

## Residual Risks And Next Routing

Milestone 2 now proves Bitterroot scope resolution, f70 source-record
readiness for `R1PLAN-bitterroot-nf-12` and `R1PLAN-bitterroot-nf-13`, f70
component-inventory coverage, component adjudication, and resolver validation.
It does not prove reviewer-stack or promotion readiness. Raw
applicable-standard coverage remains red as Milestone 3 component-eval
diagnostic evidence even though the two standard gaps are classified in the
adjudication replay. The next route is Milestone 3 reviewer-stack replay:
applicability, generated rule pack, compliance review, V1 eval, component
eval, and review `phase-eval`. Bitterroot must remain profile-guidance-only
until Milestones 3-4 prove reviewer-stack readiness and registry/coverage
promotion.

## Closeout Checklist

- [ ] Verify live project and Box metadata.
- [ ] Keep `FOR-007` packet-owned and parallel to `Document_Register_Master`.
- [ ] Keep Bitterroot out of reviewer-ready registry/coverage promotion until
  review gates pass.
- [ ] Run focused tests, source-register queue audit, plan lint, and
  `git diff --check`.
- [ ] Update current routing, current-state, handoff, and agent-start docs.
- [ ] Commit the verified milestone slice atomically.
