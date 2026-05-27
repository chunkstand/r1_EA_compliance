# South Otter Example Package Milestone Plan

Date: 2026-05-27
Status: Active packet (`Milestone 0 routing and package-boundary selection
opened; Milestone 1 local package authority intake resolved locally; Milestone
2 reviewer-stack replay resolved locally; Milestone 3 registry promotion and
threshold ratchet are next. South Otter is reviewer-ready locally but still not
promoted into the governed registry, coverage manifests, or queue ledger.`)
Owner context: standalone follow-on from
`docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`

## Purpose

Open the next governed forest-specific example package around the user-selected
South Otter Landscape Restoration and Resilience Project without contaminating
the shared `Document_Register_Master` source register.

This packet starts from the official project page:

- project page:
  `https://www.fs.usda.gov/r01/custergallatin/projects/58396`
- project title:
  `South Otter Landscape Restoration and Resilience Project`
- project ID:
  `58396`
- public Pinyon/Box folder:
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158227182465`
- forest:
  `custer-gallatin-nf`
- district:
  `Ashland Ranger District`
- project status:
  `Completed`
- expected analysis type:
  `Environmental Assessment`
- decision signed date:
  `2023-06-28`

Current implementation truth:

- South Otter is not present in the active workbook by `South Otter`,
  `projects/58396`, or `58396` search at packet opening.
- South Otter is not yet a governed registry example in
  `config/forest_specific_example_package_registry_v1.json`.
- The Custer Gallatin registry row already has reviewer-ready examples through
  East Crazy and South Plateau, so South Otter must begin as a supplemental
  package-style expansion, not as a new distinct-forest coverage claim.
- The frozen review ID includes the forest slug:
  `region1-example-custer-gallatin-south-otter-58396`. Forest-specific example
  review IDs must stay tied to the applicable forest, not only to Region 1 or
  the project title.
- The future tracked eval contract must also carry the forest identity:
  `config/v1_custer_gallatin_south_otter_real_ea_eval.json`.
- Milestone 1 inventoried and downloaded the official Pinyon/Box root package
  into ignored local evidence under
  `source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/`.
  The ignored inventory and import manifest record `58` folders, `639` files,
  `2,926,223,134` bytes, and `0` download failures.
- The full Pinyon/Box root is retained as package-authority evidence, but it is
  too broad for replay because reference and implementation-review material
  mentions other Custer Gallatin districts. The replay package path is therefore
  narrowed to the official
  `Final EA and Decision Notice Documents` folder.
- The tracked replay context now lives at
  `config/replay_contexts/region1-example-custer-gallatin-south-otter-58396.json`
  and points to the current `source-set-f70ea11e04ae3d53` catalog gate plus the
  narrowed final-EA/decision package path.
- Milestone 2 resolved the reviewer stack locally. Applicability validation now
  passes with `61` applicable authorities, `335` non-applicable authorities,
  `0` unresolved authorities, and `reviewer_ready=true` after `8/8` tracked
  applicability adjudications were completed. Compliance review now reports
  `reviewer_ready=true`, `validation_passed=true`, `61` findings, and status
  counts `pass=42`, `uncertain=17`, `gap=2`.
- The tracked V1 eval contract
  `config/v1_custer_gallatin_south_otter_real_ea_eval.json` now passes with
  `contract_status="reviewer_ready"`, `broader_ea_passed=true`, and
  `forest_plan_passed=true`.
- The tracked forest-plan component eval contract
  `config/forest_plan_component_evals/region1-example-custer-gallatin-south-otter-58396.json`
  now passes all `56` cases, including all `43` raw applicable standards and
  the `5` standard-level reviewer-resolution items. The tracked component
  adjudication resolves all `169` current queue items with `132`
  `applicability_false_positive`, `37` `evidence_linking_miss`, and `0`
  real-EA omissions.
- Review `phase-eval` now passes `28/28` phases with `blockers=[]` for
  `region1-example-custer-gallatin-south-otter-58396`. The review remains
  `not_required_for_ad_hoc_review` for promotion coverage until Milestone 3
  adds governed registry and coverage entries.

## Intent Lock

South Otter is a Custer Gallatin forest-specific example. It is not a generic
Region 1 example and it is not evidence that another forest has a governed real
package.

The intended future registry identity is:

- `example_id="cgnf-south-otter-forest-specific"`
- `review_id="region1-example-custer-gallatin-south-otter-58396"`
- `forest_unit_id="custer-gallatin-nf"`
- `applicable_forest_unit_ids=["custer-gallatin-nf"]`
- `coverage_slot_id="cgnf-south-otter-forest-specific"`
- `coverage_class_id="forest_specific_reviewer_ready"`
- `queue_lineage_source_ids=[]` unless a later workbook-backed South Otter row
  is found

South Otter may become a supplemental Custer Gallatin example if it reaches
reviewer-ready status. It must not replace East Crazy as the primary Custer
Gallatin example without a separate primary-example policy decision, and it
must not increase distinct-forest coverage metrics.

## Current Evidence

- `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/SESSION_HANDOFF.md` route future forest-specific expansion through
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md` after the
  Lolo Tyler's Kitchen closeout.
- `config/forest_specific_example_package_registry_v1.json` currently has four
  governed examples: East Crazy and South Plateau for Custer Gallatin, West
  Reservoir for Flathead, and Tyler's Kitchen for Lolo.
- `config/v1_real_package_review_coverage_v1.json` currently has four
  load-bearing slots and no South Otter slot.
- The active workbook search found no South Otter match, so there is no current
  `Direct_File_Capture_Queue` row to resolve in this opening packet.
- The official project page identifies South Otter as a completed Custer
  Gallatin Environmental Assessment with project documents available through
  Pinyon/Box folder `158227182465`.
- South Otter package intake is now locally traceable: the full root inventory
  and download manifest are ignored local evidence, while the replay path is the
  official `Final EA and Decision Notice Documents` folder containing `24`
  PDFs.
- `ea-review` on the narrowed replay package passes with `24/24` extracted
  files, `1,165` package chunks, `5/5` checklist findings, and
  `reviewer_ready=true`.
- `forest-plan-resolve` on the narrowed replay package resolves the Custer
  Gallatin scope with `validation_passed=true`,
  `scope_status="custer_gallatin"`, `geographic_area_count=1`,
  `management_area_count=33`, `overlay_count=9`, and
  `unresolved_mention_count=0`.
- South Otter is now locally reviewer-ready under the Milestone 2 review stack:
  applicability, generated rule-pack, compliance review, V1 eval, component
  eval, component adjudication eval, and review `phase-eval` are green. It is
  still not a governed registry example or real-package coverage slot; that
  promotion is intentionally left to Milestone 3.

## Goal

Create a governed South Otter example package lane that can later become a
reviewer-ready supplemental Custer Gallatin example only after package authority,
review artifacts, eval contracts, and aggregate gates are all present and green.

## Non-Goals

- Do not add South Otter project files or project-specific rows to
  `Document_Register_Master`.
- Do not mark South Otter as reviewer-ready in the registry before local
  package intake, replay context, `v1-ea-eval`, forest-plan component eval,
  and `phase-eval` pass.
- Do not ratchet real-package or forest-specific aggregate thresholds in
  Milestone 0.
- Do not claim a new distinct forest. South Otter is another Custer Gallatin
  example and must not inflate `distinct_governed_example_forest_count`.
- Do not reroute any source-register queue row unless a later workbook-backed
  row is found and the packet proves it is a project-specific example boundary.
- Do not stage ignored `source_library/` evidence unless repository policy
  changes explicitly.

## Scope

- South Otter package-boundary and review identity
- packet routing and current-state docs
- package-authority intake planning
- future tracked contracts for replay, review eval, applicability adjudication,
  forest-plan component eval, and aggregate coverage
- future registry and coverage promotion only after review-readiness gates pass

## Out Of Scope

- unrelated Custer Gallatin examples
- changes to East Crazy, South Plateau, West Reservoir, or Lolo contracts
- full-canonical source capture or catalog rebuilds
- broad reviewer-engine refactors
- manual legal conclusions or responsible-official decisions

## Owner Surfaces

- South Otter packet:
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- forest-specific umbrella:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- current routing and handoff docs:
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/AGENT_START_HERE.md`
- future replay context:
  `config/replay_contexts/region1-example-custer-gallatin-south-otter-58396.json`
- future review eval contract:
  `config/v1_custer_gallatin_south_otter_real_ea_eval.json`
- future forest-plan component eval contract:
  `config/forest_plan_component_evals/region1-example-custer-gallatin-south-otter-58396.json`
- future optional applicability adjudication:
  `config/applicability_adjudications/region1-example-custer-gallatin-south-otter-58396.json`
- future optional forest-plan component adjudication:
  `config/forest_plan_component_adjudications/region1-example-custer-gallatin-south-otter-58396.json`
- future aggregate manifests, only after review readiness:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_specific_example_package_registry_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- local ignored intake:
  `source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/`
- local ignored review outputs:
  `source_library/reviews/region1-example-custer-gallatin-south-otter-58396/`
- focused tests when tracked contracts change:
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_forest_specific_example_package_registry.py`,
  `tests/test_forest_specific_example_package_eval.py`,
  `tests/test_forest_plan_component_eval_coverage.py`,
  `tests/test_cli_eval.py`

## Placement Rules

- Freeze the review slug before intake:
  `region1-example-custer-gallatin-south-otter-58396`.
- Keep forest-specific review IDs forest-qualified. Do not use
  a forest-agnostic ID for this package because the example is relevant to
  `custer-gallatin-nf`.
- Keep South Otter registry and coverage identifiers Custer Gallatin scoped.
  Use `cgnf-south-otter-forest-specific` for the future example and coverage
  slot if the review reaches reviewer-ready status.
- Treat the Pinyon/Box folder `158227182465` as the selected root package
  boundary until a package inventory proves a narrower or broader official root
  is required.
- Keep package bytes and generated review outputs under ignored
  `source_library/` paths.
- Keep replay and eval contracts under `config/` only after the matching local
  package authority exists.
- Keep the Custer Gallatin forest row primary example as East Crazy unless a
  later packet explicitly changes primary-example policy. South Otter should be
  added as a supplemental example if it reaches reviewer-ready status.
- Preserve East Crazy and South Plateau as existing governed examples.
- Do not update `config/source_register_queue_resolution_ledger_v1.json` unless
  a workbook-backed queue identity for South Otter is found.

## Weak-Point Prevention Contract

### Weak Point 1

Weak point forecast: South Otter is promoted into the registry from a URL alone.

- Owner surface:
  `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`
- Prevention gate:
  `v1-ea-eval`, `forest-plan-component-eval`, `phase-eval`,
  `real-package-review-coverage-eval`, and
  `forest-specific-example-package-eval`
- Fail threshold:
  South Otter appears as a `review_examples` row or required coverage slot
  before the South Otter review artifacts and eval contracts pass
- Controlled violation:
  focused registry tests fail if a South Otter row is added without a matching
  real-package coverage slot and replay context
- Future-Codex misuse scenario:
  a later session edits the registry first because the official project page
  looks complete; the aggregate evals and manifest-alignment tests must reject
  that shortcut

### Weak Point 2

Weak point forecast: package intake captures only the decision file and misses
specialist, comments, analysis, or objection material.

- Owner surface:
  `source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/`,
  future replay context and package inventory
- Prevention gate:
  package inventory readback, `ea-review`, `forest-plan-resolve`, and
  package-manifest freshness checks
- Fail threshold:
  local package authority cannot trace the official root project folder or
  lacks expected official document families available from the Pinyon/Box root
- Controlled violation:
  fail intake validation if the replay context points at a decision-only
  subfolder while other official project document families are available
- Future-Codex misuse scenario:
  a later session takes the shortest PDF path to get a quick review; the
  package-inventory gate forces root-package traceability first

### Weak Point 3

Weak point forecast: South Otter inflates aggregate diversity metrics as if it
were a new forest.

- Owner surface:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_specific_example_package_registry_v1.json`
- Prevention gate:
  real-package coverage eval, forest-specific example-package eval, and
  focused manifest tests
- Fail threshold:
  `distinct_forest_count_min` or
  `distinct_governed_example_forest_count_min` is increased because of South
  Otter while `forest_unit_id` remains `custer-gallatin-nf`
- Controlled violation:
  add a focused test case that proves supplemental same-forest examples do not
  count as new forests
- Future-Codex misuse scenario:
  a future session ratchets distinct-forest coverage to look better; the
  metric checks must keep forest diversity separate from package-style depth

### Weak Point 4

Weak point forecast: South Otter becomes shared canonical source-register input
without workbook authority.

- Owner surface:
  active workbook, `config/source_register_queue_resolution_ledger_v1.json`,
  downloader/catalog docs
- Prevention gate:
  workbook search/readback and `source-register-queue-audit` if any queue row
  is touched
- Fail threshold:
  South Otter is added as a master-promotion or load row without a governed
  workbook/source-register packet
- Controlled violation:
  queue tests fail if a non-workbook South Otter project URL is treated as a
  canonical promotion source
- Future-Codex misuse scenario:
  a later session treats the project URL as downloader input; the packet keeps
  project-package intake parallel to the master source register

### Weak Point 5

Weak point forecast: a future session treats South Otter as a generic example
for any forest because the project is in Region 1.

- Owner surface:
  `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  this packet
- Prevention gate:
  focused registry and real-package coverage tests for forest identity,
  supplemented by `forest-specific-example-package-eval`
- Fail threshold:
  South Otter is promoted without `forest_unit_id="custer-gallatin-nf"` and
  `applicable_forest_unit_ids=["custer-gallatin-nf"]`, or the same slot is
  referenced by another forest row
- Controlled violation:
  add a negative fixture that points the South Otter example at a non-Custer
  forest and prove the registry/eval gate fails
- Future-Codex misuse scenario:
  a later session sees a reviewer-ready package and reuses it as generic
  forest-specific guidance; the registry contract must keep the forest binding
  explicit and fail closed if it drifts

## Milestone Sequence

### Milestone 0 - Open Packet And Freeze Boundary

Outcome label: `resolved`

1. Re-read current routing, the forest-specific umbrella packet, registry,
   real-package coverage manifest, and current handoff.
2. Verify whether South Otter exists in the active workbook or tracked config.
3. Freeze the selected package identity:
   - review ID: `region1-example-custer-gallatin-south-otter-58396`
   - project page:
     `https://www.fs.usda.gov/r01/custergallatin/projects/58396`
   - Pinyon/Box folder:
     `https://usfs-public.app.box.com/v/PinyonPublic/folder/158227182465`
   - local intake root:
     `source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/`
4. Route the current docs and handoff to this packet as the next
   forest-specific example project.
5. Commit the docs-only opening slice after plan lint and `git diff --check`.

### Milestone 1 - Local Package Authority Intake

Outcome label: `resolved` if the full official package authority is locally
inventoried, downloaded, hash-recorded, and replay-context-ready; `reduced` if
the slice stops on a named package-access blocker.

Local result: `resolved`. The full official root is locally inventoried and
downloaded with hashes; replay context is tracked against the narrowed official
`Final EA and Decision Notice Documents` package path. The original root-package
`forest-plan-resolve` attempt proved the root was too broad for automated
replay (`scope_status="ambiguous"`), while the narrowed replay package resolves
Custer Gallatin scope. Component-level reviewer resolution was Milestone 2 work
and is now resolved locally; the Milestone 1 package-intake checkpoint remains
only package-authority evidence, not a registry-promotion signal.

1. Inventory the official Pinyon/Box root folder and record the folder tree,
   file names, sizes, and hashes in ignored local evidence.
2. Download the full official root package into the local intake path while
   preserving the folder structure.
3. Write a replay context only after the local package authority exists and can
   be traced repo-relatively.
4. Run `ea-review` and `forest-plan-resolve` for
   `region1-example-custer-gallatin-south-otter-58396` on the current source set.
5. Stop as `reduced` if official documents cannot be inventoried or downloaded
   completely; route the exact package-access blocker instead of fabricating a
   partial package.

### Milestone 2 - Reviewer Stack Replay

Outcome label: `resolved` if the South Otter review stack reaches
reviewer-ready status with green `v1-ea-eval`, forest-plan component eval, and
`phase-eval`; `reduced` if a named applicability, package, or component blocker
remains.

Local result: `resolved`. The narrowed replay package now has tracked
applicability adjudication, V1 eval, forest-plan component eval, and
forest-plan component adjudication contracts. `v1-ea-eval` reports
`contract_status="reviewer_ready"`, forest-plan component eval passes `56/56`
cases, forest-plan component adjudication resolves `169/169` queue items, and
review `phase-eval` passes `28/28` phases with no blockers. No registry,
coverage, or queue-ledger promotion happened in this milestone.

1. Create `config/v1_custer_gallatin_south_otter_real_ea_eval.json` only after
   package outputs exist.
2. Run the applicability sequence:
   `applicability-authority-universe`, `applicability-context-build`,
   `applicability-retrieve`, `applicability-determine`,
   `applicability-validate`, and `applicability-generate-rule-pack`.
3. If deterministic applicability leaves unresolved decisions, export tracked
   adjudication under
   `config/applicability_adjudications/region1-example-custer-gallatin-south-otter-58396.json`
   and replay until the validation passes or the remaining blocker is named.
4. Run `compliance-review`, `v1-ea-eval`,
   `forest-plan-component-eval`, and `phase-eval`.
5. Stop as `reduced` if South Otter cannot honestly reach reviewer-ready
   status; do not weaken eval thresholds or reclassify missing artifacts as
   acceptable.

### Milestone 3 - Registry Promotion And Threshold Ratchet

Outcome label: `resolved`

1. Add South Otter to `config/v1_real_package_review_coverage_v1.json` only if
   Milestone 2 proves reviewer-ready status. Use
   `slot_id="cgnf-south-otter-forest-specific"`,
   `coverage_class_id="forest_specific_reviewer_ready"`, and
   `forest_unit_id="custer-gallatin-nf"`.
2. Add South Otter to
   `config/forest_specific_example_package_registry_v1.json` as a supplemental
   `custer-gallatin-nf` example, not a new distinct forest. Use
   `example_id="cgnf-south-otter-forest-specific"` and
   `applicable_forest_unit_ids=["custer-gallatin-nf"]`.
3. Ratchet slot and reviewer-ready thresholds if South Otter becomes
   load-bearing. Do not ratchet distinct-forest thresholds based on this
   same-forest example.
4. Add or update focused tests for the new slot, same-forest supplemental
   routing, and no-queue-row boundary.
5. Update docs, current-state, handoff, and aggregate eval outputs in the same
   verified slice.

## Required Implementation Artifacts

### Tracked, After Gates Exist

- `config/replay_contexts/region1-example-custer-gallatin-south-otter-58396.json`
- `config/v1_custer_gallatin_south_otter_real_ea_eval.json`
- `config/forest_plan_component_evals/region1-example-custer-gallatin-south-otter-58396.json`
- optional:
  `config/applicability_adjudications/region1-example-custer-gallatin-south-otter-58396.json`
- optional:
  `config/forest_plan_component_adjudications/region1-example-custer-gallatin-south-otter-58396.json`
- updates to:
  `config/v1_real_package_review_coverage_v1.json`
- updates to:
  `config/forest_specific_example_package_registry_v1.json`
- updates to:
  `config/forest_plan_component_eval_coverage_v1.json`
- focused tests proving the new slot and supplemental routing invariants

### Local Ignored Evidence

- `source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/`
- `source_library/reviews/region1-example-custer-gallatin-south-otter-58396/package/`
- `source_library/reviews/region1-example-custer-gallatin-south-otter-58396/applicability/`
- `source_library/reviews/region1-example-custer-gallatin-south-otter-58396/compliance_review.json`
- `source_library/reviews/region1-example-custer-gallatin-south-otter-58396/v1_ea_eval_results.json`
- `source_library/reviews/region1-example-custer-gallatin-south-otter-58396/forest_plan_component_eval_results.json`
- `source_library/reviews/region1-example-custer-gallatin-south-otter-58396/phase_eval_results.json`

## Required Documentation And Handoff Updates

- `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- `docs/AGENT_START_HERE.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `README.md` only if stable start-here links or durable command examples
  change

## Required Verification Gates

Milestone 0 opening:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md
git diff --check
```

Milestone 1 package intake:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path "source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/Final EA and Decision Notice Documents" \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path "source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/Final EA and Decision Notice Documents" \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --forest-unit-id custer-gallatin-nf \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --reuse-package-cache
```

Milestone 2 reviewer stack:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-context-build \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --package-path "source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/Final EA and Decision Notice Documents"

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-retrieve \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/Final EA and Decision Notice Documents" \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --forest-unit-id custer-gallatin-nf \
  --rule-pack source_library/reviews/region1-example-custer-gallatin-south-otter-58396/applicability/generated_rule_pack.json \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --eval-file config/v1_custer_gallatin_south_otter_real_ea_eval.json

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396 \
  --eval-file config/forest_plan_component_evals/region1-example-custer-gallatin-south-otter-58396.json

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-custer-gallatin-south-otter-58396
```

Milestone 3 aggregate promotion:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval \
  --output-dir source_library \
  --manifest config/forest_specific_example_package_registry_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage \
  --output-dir source_library \
  --manifest config/forest_plan_component_eval_coverage_v1.json

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_forest_specific_example_package_registry.py \
  tests/test_forest_specific_example_package_eval.py \
  tests/test_forest_plan_component_eval_coverage.py \
  tests/test_cli_eval.py

PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

If a future milestone touches queue routing, also run:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-queue-audit \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_queue_resolution.py
```

## Acceptance Criteria

- Milestone 0 acceptance is verified by
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  and `git diff --check`; both commands must pass before commit.
- Milestone 0 resolves only the packet-opening scope: South Otter has a frozen
  forest-qualified review ID, official project page, Pinyon/Box folder,
  current routing, and handoff entry.
- South Otter remains absent from governed example and coverage manifests
  until package and eval evidence exists.
- The registry and coverage manifests remain green and unchanged during the
  opening slice.
- The local package authority, once created, traces to the official Pinyon/Box
  root and preserves the official project document families.
- `region1-example-custer-gallatin-south-otter-58396` cannot be marked
  reviewer-ready unless `v1-ea-eval` and `phase-eval` pass with no blockers.
- If South Otter is promoted, it is supplemental to the Custer Gallatin row and
  does not increase distinct forest coverage.
- Future South Otter registry promotion uses
  `example_id="cgnf-south-otter-forest-specific"` and
  `applicable_forest_unit_ids=["custer-gallatin-nf"]`; no other forest row may
  reference that example.
- Docs, handoff, and current-state surfaces state the same active packet and
  residual risk before commit.

## Stop Conditions

- Stop if the Pinyon/Box root folder cannot be inventoried or downloaded
  completely.
- Stop if the official project documents are unavailable without JavaScript and
  no deterministic package-intake route exists.
- Stop if South Otter is found to be a workbook/source-register row requiring a
  different queue-governance packet.
- Stop if package replay exposes structural review-engine work outside this
  packet's owner surfaces.
- Stop if the review cannot honestly reach reviewer-ready status; record the
  blocker and keep South Otter out of the governed registry.

## Local Commit Closeout Policy

- Commit each resolved or reduced milestone slice atomically after verification.
- A milestone is not complete until verification passes, required docs and
  handoff updates are current, and the local atomic commit is created. Before
  commit, the slice is only ready-to-close.
- Stage only files touched for the South Otter packet.
- Do not stage ignored `source_library/` evidence unless repository policy
  changes explicitly.
- Push only when the user explicitly asks.

## Residual Risks And Next Routing

- Milestones 1 and 2 prove local package authority and reviewer-stack readiness,
  but they do not add a governed registry row, real-package coverage slot,
  component-coverage aggregate slot, or queue-ledger route. Milestone 3 owns
  those promotion artifacts.
- South Otter may add package-style depth for Custer Gallatin, but it will not
  reduce the remaining profile-guidance-only forest count unless a later packet
  chooses a forest without a governed example.
- Because South Otter is now locally reviewer-ready, the next routing target is
  Milestone 3 in this packet for aggregate promotion and threshold ratchet.
- If a future session needs a real package for a different forest, it must open
  a separate forest-specific example packet with that forest's own review ID,
  registry example ID, package authority, and eval contracts.

## Gap-Close Pass

- owner surfaces named:
  yes
- weak-point forecasts with prevention gates and fail thresholds:
  yes
- machine-readable truth artifacts named:
  yes
- forest-specific intent and future registry identifiers named:
  yes
- same-forest supplemental example guard included:
  yes
- current-state and handoff closeout required:
  yes
- commit policy included:
  yes
- stop conditions included:
  yes
