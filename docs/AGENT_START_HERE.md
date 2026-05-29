# Agent Start Here

Date: 2026-05-29

Use this file as the first stop for agent-driven document work in this repo.
It tells you which existing lane to use and when to refuse the request.
For non-document repo state, route through `docs/CURRENT_ROUTING.md` after this
quick read.

## First Step

Start with the dry-run planner:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources document-plan \
  --request /tmp/document_request.json \
  --output-dir source_library
```

The planner:

- validates the request against `docs/schemas/document_request_v1.schema.json`
- reads `config/document_lanes_v1.json`
- routes to exactly one supported document lane or fails closed
- writes planning-only artifacts under `source_library/document_plans/<request_id>/`
- never writes canonical lane outputs

## Active Workbook

- Active workbook: `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- Active workbook table: `Document_Register_Master`

## Parallel Example Guidance

- Forest-specific example packages are not part of
  `Document_Register_Master`.
- For benchmark/example-package work, read
  `config/forest_specific_example_package_registry_v1.json` and
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md` before
  pulling review artifacts.
- The Lolo follow-on is now resolved locally through
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`; future
  forest-specific example expansion starts from
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`.
- The active forest-specific example candidate is
  `docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`. For Bitterroot
  National Forest work, keep `bitterroot-nf` on
  `profile_eval_guidance_only` until Bitterroot Front forest-plan resolver,
  reviewer-stack gates, and registry/coverage promotion pass. Local package
  authority now exists under
  `source_library/reviews/_intake/region1-example-bitterroot-front-57341/`,
  with replay context
  `config/replay_contexts/region1-example-bitterroot-front-57341.json`, and
  base `ea-review` is green on `source-set-f70ea11e04ae3d53`. This is not
  reviewer-ready promotion proof. `FOR-007` (`Bitterroot Front Project`) is
  only a planned forest-specific example boundary in the queue ledger; do not
  treat the project page or Box root as `Document_Register_Master` input.
- The latest resolved forest-specific example packet is
  `docs/HLC_BONANZA_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`. For Helena-Lewis and
  Clark National Forest example-package review work, inspect
  `config/forest_specific_example_package_registry_v1.json` first, then use
  Bonanza as the governed primary example:
  `example_id="hlc-bonanza-forest-specific"`,
  `review_id="region1-example-helena-lewis-and-clark-bonanza-66532"`, and
  `primary_example_id="hlc-bonanza-forest-specific"` for
  `forest_unit_id="helena-lewis-and-clark-nf"`. Bonanza uses the official
  project page `https://www.fs.usda.gov/r01/helena-lewisclark/projects/66532`
  and Pinyon/Box folder
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/272939272513` as
  package authority. It is reviewer-ready on
  `source-set-f70ea11e04ae3d53`: package authority, applicability,
  compliance review, V1 eval, forest-plan component eval/adjudication, review
  `phase-eval`, real-package coverage, and forest-specific registry eval are
  green. Keep Bonanza parallel to `Document_Register_Master`; it is not a
  generic Region 1 example and must not be reused for non-HLC forests. The
  standalone component-coverage aggregate still exits red only on the inherited
  ECID source-delta slot; that is not an HLC Bonanza blocker.
- For Custer Gallatin example-package review work, use
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`. Use review ID
  `region1-example-custer-gallatin-south-otter-58396` and the official Custer
  Gallatin project page
  `https://www.fs.usda.gov/r01/custergallatin/projects/58396` as the selected
  package authority. Milestone 3 promoted South Otter as a same-forest Custer
  Gallatin registry example and required real-package plus component-coverage
  slot after locally proving the reviewer stack on
  `source-set-f70ea11e04ae3d53`: applicability, compliance review, V1 eval,
  forest-plan component eval/adjudication, and review `phase-eval` are green.
  The full Pinyon/Box root remains local ignored package-authority evidence,
  but the replay package path is narrowed to
  `source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/Final EA and Decision Notice Documents`
  because the full root contains broad references that make scope resolution
  ambiguous. South Otter remains parallel to `Document_Register_Master`; no
  source-register queue row was rerouted. The registry now uses South Otter as
  the Custer Gallatin primary example while East Crazy remains the only
  supplemental active Custer Gallatin example. South Plateau is archived as
  historical evidence only due to litigation and Forest Plan compliance
  challenge risk; do not use it as an example.
  The standalone component-coverage aggregate is still red only on the
  inherited ECID source-delta slot, but South Otter's required slot and
  review-scope `phase-eval` coverage are green.
- For Lolo National Forest example-package review work, inspect
  `config/forest_specific_example_package_registry_v1.json` first, then the
  Tyler's Kitchen review artifacts for
  `region1-example-lolo-tylers-kitchen-66344`. The registry now routes
  `lolo-nf` as `real_package_examples_available`, with
  `primary_example_id="lolo-tylers-kitchen-forest-specific"` and
  `queue_boundary_source_ids=["FOR-029"]`. The source-record identity blocker
  is predecessor evidence only: it moved tracked Lolo replay/eval config to
  the current `f70...` catalog, kept explicit identity selectors for the former
  multi-target mappings (`R1EA-018 -> USDA-007`, `R1EA-028 -> USDA-008`,
  `R1EA-124 -> FED-011`, `R1EA-137 -> FED-032`, and
  `R1EA-150 -> USFS-035`), and now proves `v1-ea-eval` reviewer-ready plus
  review `phase-eval` green at `28/28`. The predecessor
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  is now resolved through the source-record identity child: the current-workbook
  `f70...` catalog gate is not a drop-in owner for historical `5e65...`
  artifacts, direct replay override originally failed closed against the
  tracked replay context, and source-record identity was split across
  compliance and forest-plan reconciliation owners before the governed identity
  gate and replay refresh closed it.
  Then read
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  as the current-workbook source-set predecessor, then read
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`
  only as the source-register currentness stop that proved no exact current
  `5e65...` manifest exists, then read
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  only as the aligned-runtime predecessor reduced through review-local
  refresh, then read
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
  only as the exact predecessor that resolved the tracked contract split, then
  read
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
  only as the older predecessor that reduced the generic replacement lane,
  then read
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  as the resolved Tyler's Kitchen package-authority and registry promotion
  record.
- The Tyler's Kitchen packet carries the resolved `FOR-029`
  queue-boundary reroute plus packet-local `v1-ea-eval`, forest-plan component
  coverage, real-package coverage slot, forest-specific registry row, and
  aggregate threshold ratchet. Keep the package parallel to
  `Document_Register_Master`.
- The registry maps examples to `applicable_to_forest_unit_ids`, tells you
  which shared eval contracts to read first, and lists the per-review artifact
  families to read for each governed example.
- The aggregate gate for that lane is
  `forest-specific-example-package-eval`, which writes
  `source_library/reviews/forest_specific_example_package_eval/forest_specific_example_package_eval_results.json`
  and proves the typed per-forest routing status still aligns with governed
  review coverage and profile-eval fallback.

## Current Routing

- `docs/CURRENT_ROUTING.md` is the concise first stop for live repo routing.
- Live corpus/runtime truth is tracked in `docs/CURRENT_SYSTEM_STATE.md`.
- Current routed work and recent closeout facts are tracked in
  `docs/SESSION_HANDOFF.md`.
- The umbrella architecture packet in
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md` is now resolved
  through Milestone 10 Sequence 52; use `docs/CURRENT_ROUTING.md` for the
  live packet instead of older architecture follow-on references.

## Supported Lanes

- `project_sow_requirements_package`: proposed-action planning support before a complete EA review package exists; downstream command is `project-sow-package`.
- `decision_support_report`: responsible-official-facing synthesis over audited review artifacts; downstream command is `ea-consistency-document`.
- `reviewed_draft_packet`: governed reviewed-draft generation over audited review artifacts; downstream command is `draft-generate`.

## Required Inputs

- `project_sow_requirements_package`: `project_id` and `intake_path`
- `decision_support_report`: `review_id`
- `reviewed_draft_packet`: `review_id`

## Adjacent But Scoped Out

- `review-packet-index`
- `final-qa-certification`

These are real lanes, but they are not the first routed planner targets in this packet.

## Refuse These Requests

- `legal_sufficiency_determination`
- `final_agency_decision`
- `responsible_official_approval`

This repo supports auditable planning support and reviewed-draft generation. It does not generate
legal sufficiency determinations, final agency decisions, or human approvals.

## Go Deeper

- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/PROJECT_SOW_PACKAGE_RUNBOOK.md`
