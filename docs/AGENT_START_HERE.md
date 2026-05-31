# Agent Start Here

Date: 2026-05-31

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
- The latest resolved forest-specific example packet is
  `docs/KOOTENAI_TROJAN_DEFENSE_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`.
  For Kootenai National Forest example-package work, inspect
  `config/forest_specific_example_package_registry_v1.json` first, then use
  Trojan Defense as the governed primary example:
  `example_id="knf-trojan-defense-forest-specific"`,
  `review_id="region1-example-kootenai-trojan-defense-64354"`, and
  `primary_example_id="knf-trojan-defense-forest-specific"` for
  `forest_unit_id="kootenai-nf"`. The selected authorities are the official
  project page `https://www.fs.usda.gov/r01/kootenai/projects/64354` and the
  supplied Box folder
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/214150735755`.
  Package intake downloaded `74/74` files with `152,732,803` bytes and `0`
  failures; base `ea-review` passes with `74/74` extracted files and `3,750`
  package chunks. Component adjudication resolves `34/34` current queue items
  with `0` pending, applicability validation has `47` applicable authorities,
  `72` not applicable authorities, and `0` unresolved authorities, generated
  rule-pack validation has `47` rules, and compliance review is reviewer-ready
  with `47` findings. V1 eval contract
  `config/v1_kootenai_trojan_defense_real_ea_eval.json` passes, component eval
  contract
  `config/forest_plan_component_evals/region1-example-kootenai-trojan-defense-64354.json`
  passes `53/53` cases, real-package coverage is green at `11`
  reviewer-ready slots, component coverage is green at `12/12` reviews, and
  registry aggregate eval is green at `11` reviewer-ready examples across `10`
  governed forests with `profile_guidance_only_count=0`. Review `phase-eval`
  confirms `declared_review_contract=true` and
  `contract_backed_promotion_ready=true` for the Kootenai review scope but
  still exits red on inherited shared `rule_claim_binding` direct-eval debt.
  Keep Trojan Defense parallel to `Document_Register_Master`; use it only as
  the governed primary example for Kootenai National Forest work. It must not be reused for non-Kootenai forests.
- The predecessor resolved forest-specific example packet is
  `docs/DAKOTA_PRAIRIE_MEDORA_VEGETATION_MANAGEMENT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`.
  Dakota Prairie Grasslands uses Medora Vegetation Management as its governed
  primary example and remains resolved locally through Milestone 4.
- The predecessor resolved forest-specific example packet is
  `docs/NEZ_PERCE_CLEARWATER_DEAD_LAUNDRY_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`.
  For Nez Perce-Clearwater example-package work, inspect
  `config/forest_specific_example_package_registry_v1.json` first, then use
  Dead Laundry as the governed primary example:
  `example_id="npc-dead-laundry-forest-specific"`,
  `review_id="region1-example-nez-perce-clearwater-dead-laundry-57827"`, and
  `primary_example_id="npc-dead-laundry-forest-specific"` for
  `forest_unit_id="nez-perce-clearwater-nfs"`. The selected authorities are
  the official project page
  `https://www.fs.usda.gov/r01/nezperce-clearwater/projects/57827` and
  Pinyon/Box folder
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158227433225`. The
  live Box root remains objection-heavy (`2,654` visible files;
  `8,877,044,414` top-level bytes across `Analysis`, `Decision`, and
  `Scoping`), but the governed replay boundary is now narrowed and durable:
  `82` files across `13` folders with explicit exclusion of
  `Analysis/EA references` and `Decision/2023 Objection Materials Submitted`.
  `82/82` downloads succeeded, base `ea-review` passes, applicability
  validation passes with `53` applicable authorities and `0` unresolved,
  generated rule-pack validation passes with `53` rules, component
  adjudication resolves `121/121` current queue items, compliance review is
  reviewer-ready, V1 eval contract
  `config/v1_nez_perce_clearwater_dead_laundry_real_ea_eval.json` passes,
  component eval contract
  `config/forest_plan_component_evals/region1-example-nez-perce-clearwater-dead-laundry-57827.json`
  passes `134/134` cases, and review `phase-eval` passes `28/28` phases with
  `declared_review_contract=true` and
  `contract_backed_promotion_ready=true`. `FOR-034` is resolved as the
  governed Dead Laundry forest-specific example-package boundary, the real
  package and registry aggregate evals are green, the Dead Laundry
  component-coverage slot is covered and passing, and the standalone
  component-coverage aggregate is green locally after the inherited ECID
  source-delta replay contract refresh. Keep Dead Laundry parallel to
  `Document_Register_Master`; use Dead Laundry as the governed primary example
  for Nez Perce-Clearwater National Forests work, and it must not be reused for non-NPC forests.
- The predecessor resolved forest-specific example packet is
  `docs/IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`.
  For Idaho Panhandle National Forests work, inspect
  `config/forest_specific_example_package_registry_v1.json` first, then use
  Lacy Lemoosh as the governed primary example:
  `example_id="ipnf-lacy-lemoosh-forest-specific"`,
  `review_id="region1-example-idaho-panhandle-lacy-lemoosh-60853"`, and
  `primary_example_id="ipnf-lacy-lemoosh-forest-specific"` for
  `forest_unit_id="idaho-panhandle-nfs"`. The selected authorities are the
  official project page
  `https://www.fs.usda.gov/r01/idahopanhandle/projects/60853` and Pinyon/Box
  folder `https://usfs-public.app.box.com/v/PinyonPublic/folder/158229569265`.
  Local package-authority intake records `186` downloaded files,
  `553,664,116` file bytes, zero failures, and a tracked replay context at
  `config/replay_contexts/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`.
  Milestone 2 forest-plan preflight resolves `idaho_panhandle_nfs` scope,
  builds a review-local inventory with `52` components and `8` standards, and
  passes FEIS retrieval readiness after the local f70 source-delta overlay
  closed in commit `ba3718b`: `R1PLAN-idaho-panhandle-nfs-04` indexes `1,606`
  chunks and `R1PLAN-idaho-panhandle-nfs-05` indexes `991` chunks. Idaho
  area/overlay vocabulary resolves `1` geographic area, `1` management area,
  and `2` overlays. The current `36`-item component adjudication is refreshed:
  `forest-plan-component-adjudication-eval` passes with `36/36` resolved
  system-miss items, `0` pending items, and no expectation mismatches;
  `forest-plan-resolve` reports `reviewer_ready=true` and
  `validation_passed=true`. Reviewer-stack replay passes locally in commit
  `3cea9fe`: applicability adjudication resolves `9/9` conflicts, generated
  rule-pack validation reports `56` generated rules, compliance review is
  reviewer-ready, V1 eval contract
  `config/v1_idaho_panhandle_lacy_lemoosh_real_ea_eval.json` passes, component
  eval contract
  `config/forest_plan_component_evals/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`
  passes `52/52` cases, and review `phase-eval` passes `28/28` phases with
  `declared_review_contract=true` and
  `contract_backed_promotion_ready=true`. Real-package coverage and
  forest-specific registry eval are green; the standalone component-coverage
  aggregate is reduced only on the inherited ECID source-delta slot while the
  Idaho slot itself passes. Preserve `St. Maries Ranger District` as the
  authority label and `St. Joe Ranger District` as resolver scope evidence.
  Keep Lacy Lemoosh parallel to `Document_Register_Master`; use Lacy Lemoosh
  as the governed primary example for Idaho Panhandle National Forests work,
  and it must not be reused for non-Idaho-Panhandle forests.
- Beaverhead-Deerlodge South Tobacco Roots example-package work is resolved
  through Milestone 4 in
  `docs/BEAVERHEAD_DEERLODGE_SOUTH_TOBACCO_ROOTS_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`.
  For Beaverhead-Deerlodge example-package work, use review ID
  `region1-example-beaverhead-deerlodge-south-tobacco-roots-63754` and forest
  unit `beaverhead-deerlodge-nf`. The selected authorities are the official
  project page
  `https://www.fs.usda.gov/r01/beaverhead-deerlodge/projects/63754` and
  Pinyon/Box folder
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/199281418011`. This
  package authority, base review, source-record retrieval, scope validation, component
  adjudication, applicability adjudication, generated rule-pack validation,
  compliance review, V1 eval, component eval, and review `phase-eval` are
  green locally. It is now the governed primary Beaverhead-Deerlodge example:
  `example_id="bdnf-south-tobacco-roots-forest-specific"` and
  `primary_example_id="bdnf-south-tobacco-roots-forest-specific"` for
  `forest_unit_id="beaverhead-deerlodge-nf"`. Real-package coverage and
  forest-specific registry eval are green; the component-coverage aggregate is
  reduced only on inherited ECID source-delta drift, while the Beaverhead slot
  itself passes. Keep South Tobacco Roots parallel to
  `Document_Register_Master`; it is not a generic Region 1 example and must not
  be reused for non-Beaverhead-Deerlodge forests.
- The predecessor resolved forest-specific example packet before Beaverhead is
  `docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`. For Bitterroot
  National Forest example-package review work, inspect
  `config/forest_specific_example_package_registry_v1.json` first, then use
  Bitterroot Front as the governed primary example:
  `example_id="bitterroot-front-forest-specific"`,
  `review_id="region1-example-bitterroot-front-57341"`, and
  `primary_example_id="bitterroot-front-forest-specific"` for
  `forest_unit_id="bitterroot-nf"`. Bitterroot Front uses the official project
  page `https://www.fs.usda.gov/r01/bitterroot/projects/57341` and Pinyon/Box
  folder `https://usfs-public.app.box.com/v/PinyonPublic/folder/158226983588`
  as package authority. It is reviewer-ready on
  `source-set-f70ea11e04ae3d53`: package authority, applicability,
  compliance review, V1 eval, forest-plan component eval/adjudication, review
  `phase-eval`, real-package coverage, and forest-specific registry eval are
  green. `FOR-007` is resolved as a forest-specific example-package boundary.
  Keep Bitterroot Front parallel to `Document_Register_Master`; it is not a
  generic Region 1 example and must not be reused for non-Bitterroot forests.
  The standalone component-coverage aggregate still exits red only on the
  inherited ECID source-delta slot; that is not a Bitterroot blocker.
- The HLC Bonanza forest-specific example packet is resolved through
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
- Treat forest-specific example reuse as fail-closed: a governed example is
  blocked unless `v1-ea-eval` runtime forest-plan scope identifies that same
  forest as applicable. Do not use a forest-specific package as guidance for
  another forest only because the registry or package label looks similar.
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
