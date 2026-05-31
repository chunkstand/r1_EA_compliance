# Nez Perce-Clearwater Dead Laundry Example Package Milestone Plan
Date: 2026-05-30
Status: Active. `Milestone 0` packet opening and queue-boundary reroute are resolved locally;
`Milestone 1` full-tree inventory and package-authority boundary selection are next.
Plan class: implementation
High-risk implementation: yes
Owner context: standalone follow-on from `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Commit policy: each completed milestone closes only after verification, affected docs/handoff
updates, and a local atomic commit.

## Purpose

Open the governed Nez Perce-Clearwater National Forests example-package lane around the
user-selected Dead Laundry EA package without contaminating `Document_Register_Master` or claiming
reviewer-ready status before the deterministic review gates pass.

Selected package authority:

- project page: `https://www.fs.usda.gov/r01/nezperce-clearwater/projects/57827`
- project title: `Dead Laundry`
- project ID: `57827`
- public Pinyon/Box folder: `https://usfs-public.app.box.com/v/PinyonPublic/folder/158227433225`
- Box root folder label: `Dead Laundry (57827)`
- forest: `nez-perce-clearwater-nfs`
- ranger district: `North Fork Ranger District`
- expected analysis type: `Environmental Assessment`
- project status: `Completed`
- decision signed date: `2024-12-23`
- frozen review ID: `region1-example-nez-perce-clearwater-dead-laundry-57827`
- queue boundary source ID: `FOR-034`

## Intent Lock

Dead Laundry is a Nez Perce-Clearwater National Forests example candidate only. It is not a
generic Region 1 example, not a substitute for Idaho Panhandle, Lolo, Flathead, or Bitterroot
packages, and not evidence that any other forest has a governed real-package example.

The planned governed identity is:

- `example_id="npc-dead-laundry-forest-specific"`
- `review_id="region1-example-nez-perce-clearwater-dead-laundry-57827"`
- `forest_unit_id="nez-perce-clearwater-nfs"`
- `applicable_forest_unit_ids=["nez-perce-clearwater-nfs"]`
- `coverage_slot_id="npc-dead-laundry-forest-specific"`
- `coverage_class_id="forest_specific_reviewer_ready"`
- `queue_lineage_source_ids=["FOR-034"]`

`nez-perce-clearwater-nfs` must remain `profile_eval_guidance_only` in
`config/forest_specific_example_package_registry_v1.json` until Dead Laundry passes package
authority, replay context, forest-plan component/adjudication, compliance, V1 eval, review
`phase-eval`, and review-scope promotion gates. `FOR-034` should stop pretending to be a generic
master-promotion row as soon as this packet opens, but it must not resolve until reviewer-ready
promotion closes.

## Current Evidence

- Live Forest Service readback on 2026-05-30 identifies Dead Laundry as project `57827`,
  `Completed`, with expected analysis type `Environmental Assessment`, lead management unit
  `North Fork Ranger District`, and decision signed date `2024-12-23`.
- Live Box readback identifies root folder `Dead Laundry (57827)` under
  `Nez Perce Clearwater National Forest (110117)` >
  `North Fork Ranger District (11011753)`.
- The root currently exposes `Analysis` (`455` visible files; `1,802,724,968` bytes),
  `Decision` (`2,186` visible files; `6,997,388,791` bytes), and
  `Scoping` (`13` visible files; `76,930,655` bytes), totaling `2,654` visible files and
  `8,877,044,414` top-level bytes.
- `Decision` is objection-heavy: `2024 Final Decision and EA` has `10` files, but
  `2023 Objection Materials Submitted` alone has `2,158`. `Analysis` also mixes specialist reports
  and reference families, so package-authority boundary selection is still open.
- `FOR-034` now routes to this packet as planned `forest_specific_example_package` work.
- `nez-perce-clearwater-nfs` still routes `profile_eval_guidance_only`, and `FINAL-Q-NPC-001`
  remains a separate planning-record blocker.

## Goal

Create a governed Dead Laundry example-package lane for `nez-perce-clearwater-nfs`, then promote
it as the Nez Perce-Clearwater primary example only after deterministic package-authority,
forest-plan, reviewer-stack, and aggregate promotion gates are all present and green.

## Non-Goals

- Do not add Dead Laundry package files or project-specific rows to `Document_Register_Master`.
- Do not promote `nez-perce-clearwater-nfs` to `real_package_examples_available` before package
  authority, replay context, `v1-ea-eval`, forest-plan component eval, and review `phase-eval`
  pass together.
- Do not resolve `FINAL-Q-NPC-001` or reopen
  `docs/NEZ_PERCE_CLEARWATER_PLANNING_RECORD_BLOCKER_MILESTONE_PLAN.md` inside this packet.
- Do not auto-collapse the root package to a convenient local subset without preserving the full
  official inventory and a durable rationale for any narrowed replay boundary.
- Do not weaken tests, eval thresholds, validation checks, or queue/registry contracts to make NPC
  look ready.
- Do not stage ignored `source_library/` package bytes or generated review outputs unless repo
  policy changes explicitly.

## Scope

- Dead Laundry review identity, queue boundary, and routed docs/handoff
- full-tree inventory and governed package-authority boundary selection
- future replay, review, adjudication, and coverage contracts after evidence exists
- registry, coverage, and queue resolution only after reviewer-ready gates pass

## Out Of Scope

- unrelated NPC projects or the NPC planning-record blocker family
- full-canonical source capture or catalog rebuilds
- broad reviewer-engine refactors
- legal-sufficiency or responsible-official outputs

## Owner Surfaces

- packet and active docs:
  `docs/NEZ_PERCE_CLEARWATER_DEAD_LAUNDRY_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`
- queue routing and umbrella:
  `config/source_register_queue_resolution_ledger_v1.json`,
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- registry and coverage manifests, when promotion is allowed:
  `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- future replay/eval/adjudication contracts under `config/` with frozen review ID
- local intake and review outputs under
  `source_library/reviews/_intake/region1-example-nez-perce-clearwater-dead-laundry-57827/` and
  `source_library/reviews/region1-example-nez-perce-clearwater-dead-laundry-57827/`
- focused tests:
  `tests/test_source_register_queue_resolution.py`,
  `tests/test_forest_specific_example_package_registry.py`

## Intent Hierarchy

- Invariant: Dead Laundry remains parallel to `Document_Register_Master` unless a separate
  workbook/source-register packet proves direct shared-source promotion.
- Optimization target: keep the packet identity, `FOR-034` queue routing, active docs/handoff, and
  future replay slug aligned before any large local intake starts.
- Acceptable tradeoffs: Milestone 0 may stop before local package download if the full root first
  needs inventory and a governed boundary decision.
- Non-negotiables: do not resolve `FOR-034` early, do not promote the NPC registry row early, do
  not weaken queue or eval contracts, and do not silently drop objection/reference material from
  package-authority truth.

## Placement Rules

- Freeze review slug `region1-example-nez-perce-clearwater-dead-laundry-57827` in Milestone 0.
- Keep `FOR-034` planned under this packet until reviewer-ready promotion closes.
- Keep `nez-perce-clearwater-nfs` `profile_eval_guidance_only` until review-scope promotion gates
  pass.
- Inventory the full official Box root before choosing any narrower replay package.
- Keep package bytes and review outputs under ignored `source_library/` paths on
  `source-set-f70ea11e04ae3d53`.

## Weak-Point Prevention Contract

### Weak Point 1

- Owner surface:
  queue ledger and `Document_Register_Master`
- Prevention gate:
  `source-register-queue-audit` plus focused queue-routing tests
- Fail threshold:
  `FOR-034` still reads `promote_direct_file` after Milestone 0 or any Dead Laundry file enters the
  master
- Controlled violation:
  keep `FOR-034` planned under this packet until reviewer-ready promotion closes
- Future-Codex misuse scenario:
  a later session bulk-promotes project files because the queue row still looks canonical

### Weak Point 2

- Owner surface:
  forest-specific registry and real-package coverage manifests
- Prevention gate:
  `phase-eval`, V1 eval, component eval/adjudication, and aggregate coverage evals
- Fail threshold:
  `nez-perce-clearwater-nfs` leaves `profile_eval_guidance_only` early
- Controlled violation:
  keep the packet active but registry-unpromoted
- Future-Codex misuse scenario:
  a later session promotes NPC from inventory/download evidence alone

### Weak Point 3

- Owner surface:
  live Box inventory, intake manifest, and replay-context package path
- Prevention gate:
  full-tree inventory plus explicit boundary rationale before `ea-review`
- Fail threshold:
  local intake starts from an arbitrary child folder with no full-root record
- Controlled violation:
  Milestone 1 may end `reduced` if boundary choice remains unresolved
- Future-Codex misuse scenario:
  a later session silently drops objection/reference families and cannot explain the authority loss

### Weak Point 4

- Owner surface:
  replay context, resolver inputs, and the NPC planning-record blocker packet
- Prevention gate:
  frozen `forest_unit_id="nez-perce-clearwater-nfs"` plus `forest-plan-resolve`
- Fail threshold:
  the packet borrows another forest's example or starts absorbing `FINAL-Q-NPC-001`
- Controlled violation:
  stop on a typed blocker rather than weakening resolver validation
- Future-Codex misuse scenario:
  a later session loses forest-qualified traceability by mixing project and planning-record lanes

## Milestone Sequence

### Milestone 0 - Open Packet And Freeze Boundary

Outcome label: `resolved`

Local result: resolved. Dead Laundry is now a tracked active packet, `FOR-034` no longer routes as
generic direct-file promotion work, and the active routing/state/handoff surfaces point at this
packet while `nez-perce-clearwater-nfs` remains `profile_eval_guidance_only`.

1. Verify project and Box metadata, then freeze review identity and URLs.
2. Reroute `FOR-034` to this packet as planned `forest_specific_example_package` work.
3. Keep the registry unpromoted and update routing/state/handoff/umbrella docs.
4. Verify with plan lint, focused tests, queue audit, forest-specific example-package eval, and
   `git diff --check`.

### Milestone 1 - Inventory And Boundary Choice

Outcome label: `resolved` if authoritative full-tree inventory plus chosen replay boundary are
durable; `reduced` if inventory proves a narrower governed replay package is required before local
download.

1. Inventory the full official Box tree with file IDs, names, sizes, folder URLs, and counts.
2. Preserve full-root evidence before selecting any narrowed replay package.
3. Stop `reduced` if the package cannot be inventoried reproducibly or the boundary cannot be
   chosen without guessing.

### Milestone 2 - Local Intake And Base Review

Outcome label: `resolved` if the governed package boundary downloads with hashes and base
`ea-review` passes; `reduced` if any official files inside the governed boundary cannot be
downloaded or hashed.

1. Download the governed package boundary under the frozen review slug.
2. Write `box_inventory.json` and `box_import_manifest.json`.
3. Add replay context only after local package authority exists.
4. Run base `ea-review` on `source-set-f70ea11e04ae3d53`.

### Milestone 3 - Forest-Plan And Reviewer Stack Replay

Outcome label: `resolved` if NPC scope, applicability, compliance, V1, component eval, and review
`phase-eval` are green; `reduced` if a named source-readiness, adjudication, or replay blocker
remains.

1. Build a review-local NPC component inventory and run `forest-plan-resolve`.
2. Resolve any tracked applicability/component adjudications and replay the reviewer stack.
3. Keep registry and coverage manifests unpromoted if any gate stays red.

### Milestone 4 - Promotion And Queue Resolution

Outcome label: `resolved` for NPC promotion; `reduced` only if a pre-existing aggregate blocker
outside the Dead Laundry slot remains.

1. Add Dead Laundry to real-package coverage, the forest-specific registry, and component coverage.
2. Resolve `FOR-034` as `forest_specific_example_package`.
3. Rerun review-scope and aggregate promotion gates.
4. Update docs/handoff and commit the promotion slice atomically.

## Required Verification Gates

Use the milestone-appropriate subset of these gates:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/NEZ_PERCE_CLEARWATER_DEAD_LAUNDRY_EXAMPLE_PACKAGE_MILESTONE_PLAN.md --strict
PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_queue_resolution.py tests/test_forest_specific_example_package_registry.py
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
git diff --check
```

Later milestones add packet-specific `ea-review`, `forest-plan-resolve`, `phase-eval`,
`real-package-review-coverage-eval`, and matching applicability/compliance/component gates using
the frozen review ID and the chosen governed package boundary.

## Acceptance Criteria

- Dead Laundry has a forest-qualified packet, review ID, and queue-boundary owner before local
  intake begins.
- `FOR-034` no longer pretends to be generic direct-file promotion work after Milestone 0, but it
  resolves only when reviewer-ready promotion closes.
- `nez-perce-clearwater-nfs` remains `profile_eval_guidance_only` until deterministic reviewer
  gates pass together.
- Any narrowed replay package preserves the full-root inventory truth and explicit include/exclude
  rationale.
- Future promotion lands registry, coverage manifests, queue resolution, docs, handoff, and
  review-scope gates in one milestone closeout.

## Stop Conditions

- Official project-page and Box identity drift away from Dead Laundry project `57827`.
- The full root or any proposed narrowed boundary cannot be inventoried or downloaded
  reproducibly.
- The governed replay package resolves to a forest other than
  `nez-perce-clearwater-nfs`.
- Reviewer-ready status requires weakening validation, eval thresholds, or queue/registry
  contracts.
- `FOR-034` resolves or the NPC registry row promotes before review `phase-eval` and
  aggregate promotion gates pass.

## Closeout Outcome Record

- `Milestone 0`: 2026-05-30 project/Box readback froze
  `review_id="region1-example-nez-perce-clearwater-dead-laundry-57827"`; `FOR-034` rerouted to
  this packet as planned `forest_specific_example_package` work; plan lint, focused tests, queue
  audit, `forest-specific-example-package-eval`, and `git diff --check` passed.

## Gap-Close Verification Addendum

Milestone 0 is gap-closed only while the packet, queue ledger, active routing docs, and handoff
agree that Dead Laundry is the active NPC example follow-on, `FOR-034` is packet-owned planned
example work, `nez-perce-clearwater-nfs` remains `profile_eval_guidance_only`, and the next route
is full-tree inventory plus governed package-authority boundary selection before replay context or
review-promotion claims.
