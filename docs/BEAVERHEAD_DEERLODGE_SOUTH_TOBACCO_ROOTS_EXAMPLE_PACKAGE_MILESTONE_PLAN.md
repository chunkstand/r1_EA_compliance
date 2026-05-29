# Beaverhead-Deerlodge South Tobacco Roots Example Package Milestone Plan

Date: 2026-05-29
Status: Reduced locally through Milestone 2 forest-plan resolver preflight. Package authority,
base `ea-review`, review-local component inventory, forest scope, and source-record retrieval are
resolved; component adjudication and reviewer-stack replay remain open before any registry or
coverage promotion.
Plan class: implementation
Owner context: standalone follow-on from `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Intent lock: `review_id="region1-example-beaverhead-deerlodge-south-tobacco-roots-63754"` is only
for Beaverhead-Deerlodge National Forest South Tobacco Roots package work.

## Purpose

Open the governed Beaverhead-Deerlodge National Forest example-package lane around the
user-selected South Tobacco Roots Vegetation Management Project package without contaminating
`Document_Register_Master` or claiming reviewer-ready status before deterministic gates pass.

Selected package authority:

- project page: `https://www.fs.usda.gov/r01/beaverhead-deerlodge/projects/63754`
- project title: `South Tobacco Roots Vegetation Management Project`
- project ID: `63754`
- public Pinyon/Box folder: `https://usfs-public.app.box.com/v/PinyonPublic/folder/199281418011`
- Box root folder label: `South Tobacco Roots Vegetation Management Project (63754)`
- forest: `beaverhead-deerlodge-nf`
- ranger district: `Madison Ranger District`
- expected analysis type: `Environmental Assessment`
- selected package folder: `Final EA and FONSI`
- frozen review ID: `region1-example-beaverhead-deerlodge-south-tobacco-roots-63754`

## Intent Hierarchy

- Invariant: South Tobacco Roots remains a forest-specific Beaverhead-Deerlodge example package,
  not a generic Region 1 example and not a master-register source-capture input.
- Optimization target: prove replayable local package authority and resolver readiness first, then
  move to component adjudication and reviewer-stack gates only if evidence remains deterministic.
- Acceptable tradeoffs: a reduced checkpoint is better than premature registry promotion when
  component findings or eval artifacts are incomplete.
- Explicit non-negotiables: do not weaken tests, evals, component gates, or registry thresholds to
  get a green result; do not stage ignored `source_library/` bytes.

## Intent Lock

The planned governed identity is:

- `example_id="bdnf-south-tobacco-roots-forest-specific"`
- `review_id="region1-example-beaverhead-deerlodge-south-tobacco-roots-63754"`
- `forest_unit_id="beaverhead-deerlodge-nf"`
- `applicable_forest_unit_ids=["beaverhead-deerlodge-nf"]`
- `coverage_slot_id="bdnf-south-tobacco-roots-forest-specific"`
- `coverage_class_id="forest_specific_reviewer_ready"`
- `queue_lineage_source_ids=[]` unless a later workbook-backed South Tobacco Roots queue row is
  found

Beaverhead-Deerlodge remains `profile_eval_guidance_only` in
`config/forest_specific_example_package_registry_v1.json` until South Tobacco Roots passes
package authority, replay context, forest-plan component adjudication, compliance, V1 eval,
phase eval, and review-scope promotion gates.

## Current Evidence

- `config/forest_specific_example_package_registry_v1.json` still routes
  `beaverhead-deerlodge-nf` as `profile_eval_guidance_only` with no primary or supplemental real
  package example.
- The official Box root has been inventoried and downloaded under ignored local evidence at
  `source_library/reviews/_intake/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754/`.
- `box_inventory.json` records root folder `199281418011`, root label
  `South Tobacco Roots Vegetation Management Project (63754)`, folder `Final EA and FONSI`,
  `16` visible files, and `176,594,060` expected bytes.
- `box_import_manifest.json` records `16` downloaded files, `176,594,060` actual bytes, and
  `failure_count=0`.
- `ea-review` on the full package passed with `16/16` extracted files, `1,382` package chunks,
  `package_failed_count=0`, `finding_status_counts={"pass":5}`, `validation_passed=true`, and
  `reviewer_ready=true`.
- Beaverhead-Deerlodge single-forest component inventory was built as review-local generated
  evidence with `90` components, `89` standards, `coverage_passed=true`, and
  `component_source_accuracy_passed=true`.
- Beaverhead-Deerlodge profile terms now include South Tobacco Root aliases for the
  `Tobacco Root Landscape`, and the resolver ignores the Helena-Lewis and Clark comparison phrase
  in this package as external background evidence rather than project-location scope.
- `forest-plan-resolve` now reports `scope_status="beaverhead_deerlodge_nf"`,
  `validation_passed=true`, `geographic_area_count=2`, `management_area_count=3`,
  `overlay_count=2`, `project_location_signal_count=3`, `unresolved_mention_count=0`, and
  `supporting_plan_evidence_count=6`.
- Retrieval readiness is green for the Beaverhead-Deerlodge source records required by the
  selected plan routes on `source-set-f70ea11e04ae3d53`.
- The same resolver run remains `reviewer_ready=false` because component adjudication is not
  closed: raw component evaluation reports `component_count=90`, `applicable_count=90`,
  `applicable_standard_count=89`, `supported_count=30`, `gap_count=60`,
  `reviewer_resolution_count=60`, `applicable_standard_coverage_passed=false`,
  `all_applicable_standards_applied=false`, and component adjudication fails on
  `adjudication_eval_missing`.

## Goal

Begin a governed South Tobacco Roots example package lane for Beaverhead-Deerlodge and stop at the
first truthful reduced checkpoint if the deterministic reviewer stack is not ready.

## Non-Goals

- Do not add South Tobacco Roots package files or project-specific rows to `Document_Register_Master`.
- Do not promote Beaverhead-Deerlodge in the forest-specific registry, real-package coverage, or
  component-coverage manifests until reviewer-stack gates pass.
- Do not overwrite shared f70 component inventory to support this package; use review-local
  generated evidence unless a later shared-inventory milestone owns that change.
- Do not weaken forest-plan resolver validation, real-package coverage thresholds, component
  adjudication evals, or profile eval tests to get green.
- Do not stage ignored `source_library/` package bytes or generated review outputs unless repo
  policy changes explicitly.

## Scope

- Beaverhead-Deerlodge South Tobacco Roots package boundary and review identity
- local ignored package-authority intake and generated review evidence
- tracked replay context for the selected package
- Beaverhead-Deerlodge profile aliases and resolver external-comparison guard needed to make the
  official package preflight deterministic
- docs and handoff routing to this active packet
- focused tests preserving the no-promotion boundary

## Out Of Scope

- unrelated Beaverhead-Deerlodge projects
- unrelated profile-only forests
- workbook source-register promotion
- global component-inventory promotion
- registry threshold ratchets before South Tobacco Roots is reviewer-ready

## Owner Surfaces

- packet: `docs/BEAVERHEAD_DEERLODGE_SOUTH_TOBACCO_ROOTS_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- replay context:
  `config/replay_contexts/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754.json`
- forest-specific umbrella: `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- profile terms: `config/forest_plan_profiles.json`
- resolver scope guard: `src/usfs_r1_ea_sources/forest_plan_resolver_location.py`
- generated local intake:
  `source_library/reviews/_intake/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754/`
- generated local review outputs:
  `source_library/reviews/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754/`
- future promotion manifests, when allowed:
  `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- docs:
  `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`
- tests:
  `tests/test_replay_context.py`, `tests/test_forest_plan_profiles.py`,
  `tests/test_forest_plan_resolver_profiles.py`,
  `tests/support/compliance_component_fixtures.py`

## Placement Rules

- Freeze the review slug as
  `region1-example-beaverhead-deerlodge-south-tobacco-roots-63754`.
- Keep Beaverhead-Deerlodge identifiers forest-qualified; do not use a generic
  `region1-example-south-tobacco-roots` review ID.
- Use `source-set-f70ea11e04ae3d53` and the repo-root current catalog for the tracked replay
  context.
- Keep the full Box root as package-authority evidence unless a later milestone proves a narrower
  replay package is required.
- Keep generated package bytes and review outputs under ignored `source_library/` paths.
- Keep Beaverhead-Deerlodge registry status as `profile_eval_guidance_only` until reviewer-ready
  promotion gates pass.

## Weak-Point Prevention Contract

### Weak Point 1

Weak point forecast: South Tobacco Roots is promoted from URL/package authority alone.

- Owner surface: `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`
- Prevention gate: component adjudication eval, V1 eval, compliance review, component eval,
  phase eval, real-package coverage eval, and forest-specific example-package eval
- Fail threshold: Beaverhead-Deerlodge gets a primary example or required coverage slot before
  reviewer-stack gates pass
- Controlled violation: registry and coverage evals must fail if a future change adds the slot
  without matching reviewer-ready artifacts
- Future-Codex misuse scenario: a future session sees `ea-review` green and promotes the package;
  this packet records that Milestone 2 is reduced while component adjudication remains missing

### Weak Point 2

Weak point forecast: external Helena-Lewis and Clark comparison text is treated as project scope.

- Owner surface: `src/usfs_r1_ea_sources/forest_plan_resolver_location.py` and
  `tests/test_forest_plan_resolver_profiles.py`
- Prevention gate: focused resolver profile regression for South Tobacco Roots comparison context
- Fail threshold: resolver reports `multiple_forest_units_mentioned` or resolves HLC as project
  location for this Beaverhead-Deerlodge package
- Controlled violation: the regression fixture includes an HLC comparison sentence and must still
  pass with `scope_status="beaverhead_deerlodge_nf"`
- Future-Codex misuse scenario: a future rule treats every forest name as project-location
  evidence and makes Beaverhead packages ambiguous again

### Weak Point 3

Weak point forecast: component scope is mistaken for reviewer-ready component compliance.

- Owner surface: `forest_plan_context_summary.json`, future component adjudication, and future
  component eval contract
- Prevention gate: forest-plan resolver validation plus
  `forest-plan-component-adjudication-eval` before promotion
- Fail threshold: `reviewer_ready=false`, `adjudication_eval_missing`, unresolved component queue
  items, or applicable-standard coverage failure remains
- Controlled violation: Milestone 2 preserves the typed reduced result with `60` reviewer
  resolution items instead of weakening the eval
- Future-Codex misuse scenario: a future session reads `scope_status="beaverhead_deerlodge_nf"` and
  skips the component adjudication packet

### Weak Point 4

Weak point forecast: South Tobacco Roots package intake contaminates the shared master register.

- Owner surface: active workbook, `Document_Register_Master`, source-register queue ledger, and
  downloader/catalog docs
- Prevention gate: workbook/queue search and queue audit before any source-register change
- Fail threshold: package documents are added as master-promotion rows without a governed
  workbook/source-register packet
- Controlled violation: queue tests must fail if a non-workbook South Tobacco Roots URL is treated
  as canonical promotion input
- Future-Codex misuse scenario: a later session treats the Box package as downloader input; this
  packet keeps project-package intake parallel to the master source register

## Milestone Sequence

### Milestone 0 - Open Packet And Freeze Boundary

Outcome label: `resolved`

1. Read current routing, handoff, forest-specific umbrella, registry, and real-package coverage
   manifests.
2. Freeze the South Tobacco Roots review identity and selected official project/documents URLs.
3. Verify Beaverhead-Deerlodge still has no active real-package slot.
4. Stop as `blocked` if another tracked packet already owns this same review ID.

### Milestone 1 - Local Package Authority Intake

Outcome label: `resolved`

Local result: resolved. The Box root was inventoried and downloaded with hashes. The package has
`16` files, `176,594,060` bytes, and `0` download failures. `ea-review` extracted `16/16` files
and passed validation.

1. Inventory the official Box root folder and record folder tree, file names, sizes, source folder
   URLs, and Box IDs.
2. Download visible package documents while preserving folder structure.
3. Hash every local file and record expected vs actual byte counts.
4. Build the first package cache through `ea-review`.
5. Stop as `reduced` if any official documents cannot be inventoried or downloaded completely.

### Milestone 2 - Forest-Plan Resolver Preflight

Outcome label: `reduced`

Local result: reduced. Beaverhead-Deerlodge scope, Tobacco Root landscape evidence, source-record
retrieval, and review-local component inventory are resolved, but component adjudication is not
closed. The next route is component adjudication and reviewer-stack replay.

1. Build a review-local Beaverhead-Deerlodge component inventory from the current f70 chunks.
2. Add the narrow South Tobacco Root aliases needed for profile fixture and real-package matching.
3. Add a resolver regression for HLC comparison/background text.
4. Run `forest-plan-resolve` with `--forest-unit-id beaverhead-deerlodge-nf` and the review-local
   component inventory.
5. Preserve `reduced` if component adjudication or applicable-standard coverage remains open.

### Milestone 3 - Component Adjudication And Reviewer Stack Replay

Outcome label: `future`

1. Create tracked component adjudication for the `60` reviewer-resolution items.
2. Run `forest-plan-component-adjudication-eval` until `pending_adjudication_count=0` and no
   failure categories remain.
3. Replay applicability, generated rule pack, compliance review, V1 eval, component eval, and
   review `phase-eval`.
4. Stop as `reduced` if any reviewer-stack command fails with a typed blocker.

### Milestone 4 - Registry And Coverage Promotion

Outcome label: `future`

1. Promote only after Milestone 3 is green with `reviewer_ready=true` and `blockers=[]`.
2. Add the Beaverhead-Deerlodge slot to real-package coverage, forest-specific registry, and
   component-coverage manifests.
3. Rerun aggregate evals and update current-state docs.
4. Stop if aggregate thresholds regress or if any slot is stale, source-set mismatched, or
   unsupported by review artifacts.

## Verification Gates

Executed for this reduced checkpoint:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review --package-path source_library/reviews/_intake/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-beaverhead-deerlodge-south-tobacco-roots-63754 --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library/reviews/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754/component_inventory_build --source-set-id source-set-f70ea11e04ae3d53 --source-record-id FOR-002 --forest-unit-id beaverhead-deerlodge-nf --plan-version 2009 --chunks-path source_library/derived/source-set-f70ea11e04ae3d53/chunks/chunks.jsonl
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/_intake/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-beaverhead-deerlodge-south-tobacco-roots-63754 --forest-unit-id beaverhead-deerlodge-nf --forest-plan-component-inventory-path source_library/reviews/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754/component_inventory_build/derived/source-set-f70ea11e04ae3d53/forest_plan_components/component_inventory.json --reuse-package-cache --docling-timeout-seconds 180
```

Required before local commit:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/BEAVERHEAD_DEERLODGE_SOUTH_TOBACCO_ROOTS_EXAMPLE_PACKAGE_MILESTONE_PLAN.md
PYTHONPATH=src uv run --extra dev pytest tests/test_replay_context.py tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver_profiles.py -k 'beaverhead or south_tobacco or replay_context'
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Pass threshold: focused tests and lint pass with `0` failures. The real `forest-plan-resolve`
command may exit nonzero at this checkpoint only with the documented reduced component
adjudication blocker; it must still report `validation_passed=true` and
`scope_status="beaverhead_deerlodge_nf"`.

## Acceptance Criteria

- The tracked replay context loads with review ID
  `region1-example-beaverhead-deerlodge-south-tobacco-roots-63754`,
  `forest_unit_id="beaverhead-deerlodge-nf"`, `source-set-f70ea11e04ae3d53`, and
  `source_library/catalog`.
- Package authority evidence has `16` files, `176,594,060` expected bytes, `176,594,060` actual
  bytes, and `failure_count=0`.
- Forest-plan resolver preflight reaches `scope_status="beaverhead_deerlodge_nf"` and
  `validation_passed=true`.
- The reduced state explicitly records `reviewer_ready=false`, `gap_count=60`, and
  `adjudication_eval_missing`.
- Beaverhead-Deerlodge remains `profile_eval_guidance_only`; no registry, real-package coverage,
  component-coverage, or queue ledger promotion is included in this milestone.
- Verification commands above pass, except the documented reduced resolver command exit that is
  expected until component adjudication is added.

## Documentation And Handoff

- Update `docs/CURRENT_ROUTING.md`, `docs/SESSION_HANDOFF.md`, and
  `docs/CURRENT_SYSTEM_STATE.md` with this reduced checkpoint.
- Update `docs/AGENT_START_HERE.md`, `README.md`, and the forest-specific umbrella packet so future
  agents route Beaverhead-Deerlodge through this active packet without treating it as
  reviewer-ready.
- Include the tracked replay context and focused tests in the same closeout commit.
- Do not copy generated `source_library/` bytes into tracked docs; cite counts and artifact paths
  instead.

## Commit Closeout

The milestone is not complete until an atomic local commit records the verified reduced checkpoint.
Stage only the verified Beaverhead-Deerlodge slice, including implementation, tests, replay
context, packet, and affected docs. Do not stage unrelated files or ignored generated package
bytes. Push only if the user explicitly asks for a push.

## Stop Conditions

- Stop if package authority cannot be downloaded or byte counts do not match.
- Stop if forest-plan scope resolves outside `beaverhead-deerlodge-nf` or remains ambiguous after
  focused profile/context fixes.
- Stop if a required test or docs lint fails and cannot be fixed in this milestone without
  weakening a gate.
- Stop if promotion would require component adjudication, V1 eval, compliance review, or phase-eval
  work beyond this initial checkpoint.

## Residual Risks And Next Routing

- Next route: Milestone 3 component adjudication and reviewer-stack replay for
  `review_id="region1-example-beaverhead-deerlodge-south-tobacco-roots-63754"`.
- Residual risk: the `60` component findings may include true package gaps, applicability false
  positives, or evidence-linking misses; they require tracked adjudication before any promotion.
- Residual risk: aggregate component coverage still has inherited non-Beaverhead blockers in other
  slots; do not route those back into South Tobacco Roots unless the review-scope slot itself is
  failing after promotion.
- Residual risk: live project-package contents may change upstream; refresh local Box inventory
  before any future reviewer-ready promotion if the package authority timestamp becomes stale.

## Closeout Outcome Record

- Closeout status: reduced through Milestone 2, verified and committed locally after the required
  verification gate passes.
- Final commit hash: the atomic closeout commit that contains this packet; report the hash in the
  final closeout response.
- Next owner: future component adjudication and reviewer-stack replay milestone.
