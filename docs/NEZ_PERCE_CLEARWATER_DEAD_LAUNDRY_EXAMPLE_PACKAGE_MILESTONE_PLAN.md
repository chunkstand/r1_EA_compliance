# Nez Perce-Clearwater Dead Laundry Example Package Milestone Plan
Date: 2026-05-30
Status: Resolved locally through `Milestone 4`. Dead Laundry is now the governed Nez Perce-Clearwater primary example; the only remaining red surface is the inherited standalone ECID source-delta component-coverage aggregate outside the Dead Laundry slot.
Plan class: implementation
High-risk implementation: yes
Owner context: standalone follow-on from `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Commit policy: each completed milestone closes only after verification, affected docs/handoff
updates, and a local atomic commit.

## Purpose

Establish and preserve the governed Nez Perce-Clearwater National Forests example-package lane
around the user-selected Dead Laundry EA package without contaminating
`Document_Register_Master`. This packet is now the authoritative local record for the Dead Laundry
promotion after the deterministic review gates passed.

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

Dead Laundry is the governed Nez Perce-Clearwater National Forests example only. It is not a
generic example, not a substitute for Idaho Panhandle, Lolo, Flathead, or Bitterroot
packages, and not evidence that another forest has an example.

The governed identity is:

- `example_id="npc-dead-laundry-forest-specific"`
- `review_id="region1-example-nez-perce-clearwater-dead-laundry-57827"`
- `forest_unit_id="nez-perce-clearwater-nfs"`
- `applicable_forest_unit_ids=["nez-perce-clearwater-nfs"]`
- `coverage_slot_id="npc-dead-laundry-forest-specific"`
- `coverage_class_id="forest_specific_reviewer_ready"`
- `queue_lineage_source_ids=["FOR-034"]`

`nez-perce-clearwater-nfs` now routes `real_package_examples_available` in
`config/forest_specific_example_package_registry_v1.json`, and `FOR-034` now resolves as the
Dead Laundry forest-specific example-package boundary. Keep Dead Laundry parallel to
`Document_Register_Master`, do not reuse it for non-NPC forests, and keep `FINAL-Q-NPC-001`
separate as the planning-record blocker lane.

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
- The governed replay boundary is durable in `box_inventory.json` and
  `box_import_manifest.json`: `82` files across `13` folders and
  `234,693,626` bytes, with `Analysis/EA references` and
  `Decision/2023 Objection Materials Submitted` excluded.
- Replay context exists, base `ea-review` passes, and `forest-plan-resolve`
  passes with `scope_status="nez_perce_clearwater_nfs"`,
  `validation_passed=true`, `overlay_count=2`, and
  `needs_reviewer_resolution=false`.
- Applicability validation passes with `53` applicable authorities,
  `147` not-applicable authorities, and `0` unresolved authorities; generated
  rule-pack validation passes with `53` rules.
- Component adjudication resolves `121/121` current queue items, and
  `compliance-review` is reviewer-ready with `53` findings (`33` `pass`,
  `19` `uncertain`, `1` `gap`) plus matrix/PDF artifacts.
- V1 eval contract
  `config/v1_nez_perce_clearwater_dead_laundry_real_ea_eval.json` passes with
  contract status `reviewer_ready`; component eval contract
  `config/forest_plan_component_evals/region1-example-nez-perce-clearwater-dead-laundry-57827.json`
  passes `134/134` cases with `21` applicable standards; review `phase-eval`
  passes `28/28` phases with `declared_review_contract=true` and
  `contract_backed_promotion_ready=true`.
- `FOR-034` is resolved as `forest_specific_example_package` work, and
  `nez-perce-clearwater-nfs` now routes `real_package_examples_available` with
  `primary_example_id="npc-dead-laundry-forest-specific"`.
- Aggregate promotion gates are green locally:
  `real-package-review-coverage-eval` passes with `covered_slot_count=9`,
  `reviewer_ready_slot_count=9`, `distinct_forest_count=8`, and
  `distinct_package_style_count=14`; `forest-specific-example-package-eval`
  passes with `review_example_count=9`, `reviewer_ready_example_count=9`,
  `distinct_governed_example_forest_count=8`, and
  `profile_guidance_only_count=2`.
- The Dead Laundry component-coverage slot is covered, source-set aligned, and
  passing; the standalone `forest-plan-component-eval-coverage` aggregate now
  passes locally after the inherited `v1-cg-ecid-source-delta-review`
  contracts were refreshed to archived merged source set
  `source-set-8a4005c8a083af1a`.
- `FINAL-Q-NPC-001` remains a separate planning-record blocker.

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

- Dead Laundry review identity, queue boundary, governed package-authority boundary, replay/eval
  contracts, and the routed docs/handoff surfaces.
- Registry, coverage, and queue resolution only after deterministic reviewer-ready gates pass.

## Out Of Scope

- unrelated NPC projects or the NPC planning-record blocker family
- full-canonical source capture or catalog rebuilds
- broad reviewer-engine refactors
- legal-sufficiency or responsible-official outputs

## Owner Surfaces

- packet and live docs: `docs/NEZ_PERCE_CLEARWATER_DEAD_LAUNDRY_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`
- queue and umbrella: `config/source_register_queue_resolution_ledger_v1.json`,
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- governed promotion manifests: `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- frozen review contracts and local evidence under `config/` and
  `source_library/reviews/{_intake/,}region1-example-nez-perce-clearwater-dead-laundry-57827/`
- focused tests: `tests/test_nez_perce_clearwater_dead_laundry_contracts.py`,
  `tests/test_source_register_queue_resolution.py`,
  `tests/test_forest_specific_example_package_registry.py`

## Intent Hierarchy

- Invariant: Dead Laundry stays parallel to `Document_Register_Master` unless a separate
  workbook/source-register packet proves direct shared-source promotion.
- Optimization target: keep the packet identity, `FOR-034`, the docs/handoff, and the frozen review
  slug aligned.
- Acceptable tradeoff: a milestone may stop reduced rather than weaken queue or eval truth.
- Non-negotiables: no early queue resolution, no early registry promotion, no weakened gates, and
  no silent objection/reference-material loss.

## Placement Rules

- Freeze review slug `region1-example-nez-perce-clearwater-dead-laundry-57827` in Milestone 0.
- Keep `FOR-034` packet-owned until reviewer-ready promotion closes.
- Keep the package parallel to `Document_Register_Master`; keep `FINAL-Q-NPC-001` outside this
  packet.
- Inventory the full official Box root before choosing any narrower replay package.
- Keep package bytes and review outputs under ignored `source_library/` paths on
  `source-set-f70ea11e04ae3d53`.

## Weak-Point Prevention Contract

### Weak Point 1

- Owner surface: queue ledger and `Document_Register_Master`.
- Prevention gate: `source-register-queue-audit` plus focused queue-routing tests.
- Fail threshold: `FOR-034` still reads `promote_direct_file`, or any Dead Laundry file enters the
  master early.

### Weak Point 2

- Owner surface: forest-specific registry and coverage manifests.
- Prevention gate: `phase-eval`, V1 eval, component eval/adjudication, and aggregate coverage evals.
- Fail threshold: NPC promotion lands before the review-scope gates are green together.

### Weak Point 3

- Owner surface: live Box inventory, intake manifest, and replay-context package path.
- Prevention gate: full-tree inventory plus explicit boundary rationale before `ea-review`.
- Fail threshold: local intake starts from an arbitrary child folder with no full-root record.

### Weak Point 4

- Owner surface: replay context, resolver inputs, and the NPC planning-record blocker packet.
- Prevention gate: frozen `forest_unit_id="nez-perce-clearwater-nfs"` plus `forest-plan-resolve`.
- Fail threshold: the packet borrows another forest's example or absorbs `FINAL-Q-NPC-001`.

## Milestone Sequence

### Milestone 0 - Open Packet And Freeze Boundary

Outcome label: `resolved`

Local result: resolved. Dead Laundry became a tracked packet, `FOR-034` stopped routing as generic
direct-file promotion work, and the routing/state/handoff surfaces aligned to the packet.

1. Verify project and Box metadata; freeze review identity and URLs.
2. Reroute `FOR-034`; update routing/state/handoff/umbrella docs.
3. Verify with plan lint, focused tests, queue audit, registry eval, and `git diff --check`.

### Milestone 1 - Inventory And Boundary Choice

Outcome label: `resolved` if authoritative full-tree inventory plus chosen replay boundary are
durable; `reduced` if inventory proves a narrower governed replay package is required before local
download.

1. Inventory the full official Box tree and preserve the root evidence.
2. Select the narrowed replay package only with explicit include/exclude rationale.
3. Stop reduced if reproducible inventory or boundary choice is not possible.

### Milestone 2 - Local Intake And Base Review

Outcome label: `resolved` if the governed package boundary downloads with hashes and base
`ea-review` passes; `reduced` if any official files inside the governed boundary cannot be
downloaded or hashed.

1. Download the governed package boundary under the frozen review slug.
2. Write `box_inventory.json`, `box_import_manifest.json`, and replay context.
3. Run base `ea-review` on `source-set-f70ea11e04ae3d53`.

### Milestone 3 - Forest-Plan And Reviewer Stack Replay

Outcome label: `resolved` if NPC scope, applicability, compliance, V1, component eval, and review
`phase-eval` are green; `reduced` if a named source-readiness, adjudication, or replay blocker
remains.

1. Build the review-local NPC component inventory and run `forest-plan-resolve`.
2. Resolve applicability/component adjudications and replay the reviewer stack.
3. Keep promotion surfaces closed if any gate stays red.

### Milestone 4 - Promotion And Queue Resolution

Outcome label: `resolved` for NPC promotion; `reduced` only if a pre-existing aggregate blocker
outside the Dead Laundry slot remains.

1. Add Dead Laundry to real-package coverage, the forest-specific registry, and component coverage.
2. Resolve `FOR-034`, rerun promotion gates, and update docs/handoff atomically.

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

- Dead Laundry has a forest-qualified packet, review ID, and queue-boundary owner.
- `FOR-034` resolves only with reviewer-ready promotion.
- Any narrowed replay package preserves full-root inventory truth and explicit include/exclude
  rationale.
- Registry, coverage manifests, queue resolution, docs, handoff, and review-scope gates close
  together.

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

- `Milestone 0`: 2026-05-30 froze
  `review_id="region1-example-nez-perce-clearwater-dead-laundry-57827"`; `FOR-034` rerouted to
  this packet as `forest_specific_example_package` work; plan lint, tests, queue audit,
  registry eval, and `git diff --check` passed.
- `Milestone 3`: applicability adjudication, generated rule-pack validation,
  component adjudication, compliance review, V1 eval, component eval, and
  review `phase-eval` all resolved locally. Component adjudication now closes
  `121/121` current queue items; component eval passes `134/134` cases; review
  `phase-eval` passes `28/28` with `declared_review_contract=true` and
  `contract_backed_promotion_ready=true`.
- `Milestone 4`: Dead Laundry promoted into
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_specific_example_package_registry_v1.json`, and
  `config/forest_plan_component_eval_coverage_v1.json`; `FOR-034` resolved as
  forest-specific example-package boundary work; aggregate promotion gates pass
  with `covered_slot_count=9`, `reviewer_ready_slot_count=9`,
  `review_example_count=9`, `reviewer_ready_example_count=9`,
  `distinct_governed_example_forest_count=8`, and
  `profile_guidance_only_count=2`.

## Gap-Close Verification Addendum

Gap-closed with Dead Laundry now the governed NPC primary example, `FOR-034`
resolved as forest-specific example-package boundary work, and the only
remaining red surface reduced to the inherited standalone ECID source-delta
component-coverage aggregate outside the Dead Laundry slot.
