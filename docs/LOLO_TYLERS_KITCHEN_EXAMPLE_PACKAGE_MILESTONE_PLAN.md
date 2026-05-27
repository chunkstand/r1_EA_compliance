# Lolo Tyler's Kitchen Example Package Milestone Plan

Date: 2026-05-24
Status: Resolved locally (`Milestones 0-2 are preserved as
package-authority and registry closeout context; the downstream
contract/currentness/source-record blocker chain is resolved locally on
source-set-f70ea11e04ae3d53; Milestone 3 registry promotion, aggregate
threshold ratchet, and queue reroute are implemented and verified`)
Owner context: broader standalone follow-on from
`docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`

## Latest Historical Alignment Note

- This packet's Milestone 3 is now resolved locally. The downstream blocker
  chain that used to keep the Lolo row in `profile_eval_guidance_only`
  resolved first: the tracked replay context and `v1-ea-eval` contract point
  at `source-set-f70ea11e04ae3d53`, `v1-ea-eval` is
  `contract_status="reviewer_ready"`, and review `phase-eval` passes `28/28`
  with no blockers. This milestone then promoted Lolo into the governed
  forest-specific registry, ratcheted the real-package and forest-specific
  aggregate thresholds, and resolved `FOR-029` as a
  `forest_specific_example_package` queue boundary.
- Live work therefore first continued in
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  but that packet then reduced further into the exact child owner at that
  checkpoint:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
  which owns the current tracked source-set contract split for the replacement
  candidate. That narrower reroute closeout landed in `013b5d1`
  (`Open Lolo source-set contract blocker`). The active child packet then
  realigned the tracked replay context and review eval contract to `5e65...`,
  reduced Milestone 2 locally in `e2b6941`
  (`Reduce Lolo source-set blocker Milestone 2`), and resolved Milestone 3 by
  routing the residual red into
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  in `a7b4141` (`Open Lolo aligned runtime rebaseline blocker`).
- The aligned-runtime/currentness/current-workbook/source-record child chain is
  now historical after the source-record identity packet moved the tracked Lolo
  replay/eval surfaces to `f70...` and proved final green readback. This packet
  is now the resolved Tyler's Kitchen package-authority, queue-boundary, and
  forest-registry promotion record. Future forest-specific examples should
  start from `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
  or a new standalone packet rather than reopening this Lolo milestone unless
  a verified Lolo gate regresses.

## Purpose

Fully ingest the user-selected Lolo package
`Tyler's Kitchen Fuels Reduction and Forest Health Project (66344)` as a
governed forest-specific example for `lolo-nf` without contaminating
`Document_Register_Master`.

Under the current boundary, "fully ingested" for this lane means:

- the full root project package, including specialist/supporting material, is
  preserved locally as the package authority;
- the review-scoped applicability, compliance, V1, component-eval, and
  phase-eval stack is replayed against that package with a fixed review ID;
- `lolo-nf` leaves `profile_eval_guidance_only` and becomes
  `real_package_examples_available` in the forest-specific registry; and
- the related project-page queue row stops pretending to be a master-promotion
  candidate.

It does not mean promoting package rows into `Document_Register_Master`.

Current local outcome:

- the full root package authority and replay identity are in place;
- the Tyler's Kitchen packet is now the example to inspect first for Lolo
  National Forest example-package work, with `lolo-nf` routed as
  `real_package_examples_available`;
- `FOR-029` is now truthfully resolved as a packet-owned
  `forest_specific_example_package` row instead of a planned canonical
  promotion row;
- packet-local `v1-ea-eval` and `forest-plan-component-eval` are green, and
  the Lolo slot in `config/forest_plan_component_eval_coverage_v1.json` now
  expects `source-set-f70ea11e04ae3d53`;
- review-scoped `phase-eval` is now green on
  `source-set-f70ea11e04ae3d53`; and
- Milestone 3 updated the registry, coverage thresholds, queue ledger, gold
  coverage ratchets, promotion-suite checks, docs, and focused tests in one
  verified slice.

## Current Evidence

- `config/forest_specific_example_package_registry_v1.json` now routes
  `lolo-nf` as `real_package_examples_available`, with
  `primary_example_id="lolo-tylers-kitchen-forest-specific"`,
  `queue_boundary_source_ids=["FOR-029"]`, and the guidance note that Tyler's
  Kitchen should be reviewed first as the Lolo example boundary.
- `source_library/reviews/forest_specific_example_package_eval/forest_specific_example_package_eval_results.json`
  is green at `review_example_count=4`,
  `reviewer_ready_example_count=3`,
  `distinct_governed_example_forest_count=3`, and
  `profile_guidance_only_count=7`.
- `config/source_register_queue_resolution_ledger_v1.json` now routes
  `FOR-029` (`Tyler's Kitchen Fuels Reduction and Forest Health Project`) to
  this packet as `planned_disposition="forest_specific_example_package"` and
  `resolution_status="resolved"` while preserving the workbook-matching queue
  identity text.
- `config/v1_real_package_review_coverage_v1.json` now contains the required
  `lolo-tylers-kitchen-forest-specific` slot with coverage class
  `forest_specific_reviewer_ready`. The aggregate
  `real-package-review-coverage-eval` result is green at
  `covered_slot_count=4`, `reviewer_ready_slot_count=3`,
  `typed_blocked_slot_count=1`, `distinct_forest_count=3`,
  `distinct_package_style_count=4`, and no missing coverage classes.
- `config/forest_plan_component_eval_coverage_v1.json` now contains a required
  Lolo review slot aligned to `source-set-f70ea11e04ae3d53`. The aggregate
  replay still has non-Lolo red slots, so this packet must not claim aggregate
  component coverage green as part of the Lolo runtime closeout.
- `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`
  is green with `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`.
- `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`
  is green with `passed_phase_count=28`, `phase_count=28`, `blockers=[]`,
  and `identity_mismatch_phase_count=0`.
- The selected public package boundary is the root Box folder
  [Tyler's Kitchen Fuels Reduction and Forest Health Project (66344)](https://usfs-public.app.box.com/v/PinyonPublic/folder/267968720604),
  which resolves to `Lolo National Forest (110116)` >
  `Missoula Ranger District (11011603)` and currently exposes:
  - `Decision` (`3` files)
  - `Analysis` (`49` files)
  - `Consultation` (`5` files)
  - `Scoping` (`4` files)
- `FINAL-Q-LOLO-001` remains a separate full-canonical queue blocker for the
  Lolo forest-plan Pinyon library. This packet must not conflate that blocker
  family with the Tyler's Kitchen project package.

## Goal

Create the first governed Lolo real package example, routed in parallel to the
master document list, with enough deterministic review artifacts and coverage
contracts that future agents can read it as the primary `lolo-nf` example.

## Non-Goals

- Do not add Tyler's Kitchen package files or project-specific rows to
  `Document_Register_Master`.
- Do not resolve `FINAL-Q-LOLO-001` or reopen the
  `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md` lane in this packet.
- Do not weaken `forest-specific-example-package-eval`,
  `real-package-review-coverage-eval`,
  `forest-plan-component-eval-coverage`, `v1-ea-eval`, or `phase-eval` to make
  Lolo look ready.
- Do not treat the `Decision` child folder as sufficient if the root package's
  `Analysis`, `Consultation`, or `Scoping` records are missing from intake.
- Do not generalize East-Crazies-specific final-QA or signer-facing packet
  conventions unless that work is required to satisfy the minimum governed
  artifact floor for the forest-specific example lane.
- Do not stage ignored `source_library/` evidence unless repository policy
  changes explicitly.

## Scope

- queue-boundary truth for `FOR-029`
- Lolo package authority and replay identity
- per-review tracked contracts required to make the Lolo example load-bearing
- aggregate forest-specific example routing and threshold ratchets
- focused docs and tests that keep the new Lolo example discoverable and
  fail-closed

## Out Of Scope

- workbook source-row additions or removals in `Document_Register_Master`
- full-canonical source-set regeneration or downstream promotion reruns
- unrelated forest example additions for `helena-lewis-and-clark-nf`,
  `nez-perce-clearwater-nfs`, or other still-missing forests
- standalone signer-facing enrichment beyond the minimum governed example floor
  if that work turns out to require broad East-Crazies-specific generalization

## Owner Surfaces

- queue routing:
  `config/source_register_queue_resolution_ledger_v1.json`
- forest-specific registry:
  `config/forest_specific_example_package_registry_v1.json`
- real-package coverage manifest:
  `config/v1_real_package_review_coverage_v1.json`
- Lolo replay context:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
- Lolo review contract:
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`
- forest-plan component eval coverage:
  `config/forest_plan_component_eval_coverage_v1.json`
- Lolo component eval contract:
  `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`
- optional adjudication contract if deterministic applicability needs human
  replay input:
  `config/applicability_adjudications/region1-example-lolo-tylers-kitchen-66344.json`
- local ignored package authority:
  `source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344/`
- local ignored review outputs:
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/`
- docs:
  `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- tests:
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_forest_plan_component_eval_coverage.py`,
  `tests/test_forest_specific_example_package_registry.py`,
  `tests/test_forest_specific_example_package_eval.py`,
  `tests/test_source_register_queue_resolution.py`,
  `tests/test_cli_eval.py`, and
  `tests/test_architecture_contract.py`

## Placement Rules

- Freeze the review slug and replay-context filename in Milestone 0 before
  writing any review artifacts. Do not rename the review after package intake
  begins.
- The package authority must be the full root project package, not only the
  `Decision` child folder. The local intake must preserve `Decision`,
  `Analysis`, `Consultation`, and `Scoping` as sibling package inputs.
- Keep the replay context repo-relative and rooted in `source_library/` so the
  package-authority checks in aggregate evals remain deterministic.
- Keep tracked review contracts under `config/`; keep generated review outputs
  under `source_library/reviews/<review_id>/`; keep package bytes under
  `source_library/reviews/_intake/`.
- `FOR-029` must end as an explicit example-lane queue boundary row, not as a
  planned master-promotion candidate.
- `FINAL-Q-LOLO-001` must remain routed to
  `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md`; do not absorb that
  blocker into this packet.

## Weak-Point Prevention Contract

### Weak Point 1

Weak point forecast: Tyler's Kitchen is ingested as if it were shared master
input.

- Owner surface: `config/source_register_queue_resolution_ledger_v1.json`,
  `config/forest_specific_example_package_registry_v1.json`
- Prevention gate:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
  plus focused queue-routing tests
- Fail threshold: `FOR-029` remains
  `planned_disposition="promote_direct_file"` or any Lolo example routing emits
  load rows into `Document_Register_Master`
- Controlled violation: make the focused test fail if `FOR-029` is routed back
  to direct-file promotion
- Future-Codex misuse scenario: a later session sees the forest project page
  and tries to convert it into canonical source rows; the queue audit and
  registry tests must reject that move

### Weak Point 2

Weak point forecast: the package authority drops specialist/supporting record
families and keeps only decision-core PDFs.

- Owner surface:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  local intake under `source_library/reviews/_intake/`
- Prevention gate: package-inventory freshness check plus review-local package
  manifest validation through `ea-review` and `forest-plan-resolve`
- Fail threshold: the local package authority lacks one of `Decision`,
  `Analysis`, `Consultation`, or `Scoping`, or the package manifest cannot
  trace those files
- Controlled violation: fail the intake gate if the replay context points at
  the `Decision` subfolder alone
- Future-Codex misuse scenario: a later session trims the package down to the
  easiest PDFs; the replay context and package-manifest checks must catch that

### Weak Point 3

Weak point forecast: Lolo appears in the registry as governed even though the
review stack is still not reviewer-ready.

- Owner surface:
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_specific_example_package_registry_v1.json`
- Prevention gate: `v1-ea-eval`, `forest-plan-component-eval`, `phase-eval`,
  `real-package-review-coverage-eval`, and
  `forest-specific-example-package-eval`
- Fail threshold: the actual Lolo contract status is not `reviewer_ready`, the
  review artifacts are missing, or aggregate coverage only stays green because
  thresholds were not ratcheted
- Controlled violation: fail the focused tests if `lolo-nf` is moved to
  `real_package_examples_available` while the required review slot or review ID
  is absent
- Future-Codex misuse scenario: a later session edits the registry row first
  and hopes aggregate evals still pass; the ratcheted thresholds and manifest
  alignment tests must reject that

### Weak Point 4

Weak point forecast: this packet silently reopens the unrelated Lolo Pinyon
blocker family.

- Owner surface:
  `config/source_register_queue_resolution_ledger_v1.json`,
  `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md`,
  this packet doc
- Prevention gate: queue-audit plus docs/handoff alignment review
- Fail threshold: `FINAL-Q-LOLO-001` changes routing owner or Tyler's Kitchen
  references are mixed into the forest-plan Pinyon blocker packet
- Controlled violation: fail the docs alignment pass if both Lolo lanes are
  described as the same boundary
- Future-Codex misuse scenario: a future session tries to resolve both Lolo
  items in one packet; the packet routing must stay split and explicit

## Milestone Sequence

### Milestone 0 - Freshness And Boundary Rebaseline

Outcome label: `resolved`

1. Re-read the live forest-specific registry, aggregate eval result, queue
   ledger, and current routing docs.
2. Lock the selected package identity:
   - review ID: `region1-example-lolo-tylers-kitchen-66344`
   - replay context:
     `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
   - local intake root:
     `source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344/`
3. Capture the root Box inventory as the baseline package-authority truth for
   this packet and record that `FOR-029` is the related project-page queue row.
4. Route the umbrella forest-specific packet and the short routing docs to this
   standalone follow-on.

### Milestone 1 - Local Package Authority Intake

Outcome label: `resolved`

1. Download the full Tyler's Kitchen root package into the local intake path,
   preserving the folder tree and file bytes.
2. Add deterministic local package-authority metadata:
   replay context, package path, source-set identity, and package inventory
   references.
3. Run `ea-review` and `forest-plan-resolve` with the frozen review ID and the
   active source-set baseline.
4. Require the resulting package manifest/chunks to prove that the Lolo example
   uses the full root package rather than a decision-only subset.

### Milestone 2 - Reviewer-Ready Review Stack

Outcome label: `reduced`

1. Create the Lolo per-review eval contract
   `config/v1_lolo_tylers_kitchen_real_ea_eval.json`.
2. Run the applicability-first sequence against the Lolo package:
   `applicability-authority-universe`, `applicability-context-build`,
   `applicability-retrieve`, `applicability-determine`,
   `applicability-validate`, and `applicability-generate-rule-pack`.
3. If unresolved applicability decisions remain, export a tracked adjudication
   contract under
   `config/applicability_adjudications/region1-example-lolo-tylers-kitchen-66344.json`
   and replay the adjudication sequence until `applicability_validation.json`
   passes or an honest blocker remains.
4. Run `compliance-review`, `v1-ea-eval`,
   `forest-plan-component-eval`, and `phase-eval`.
5. Add the Lolo slot to `config/forest_plan_component_eval_coverage_v1.json`
   and the matching per-review contract file so review-scoped component eval is
   tracked rather than ad hoc.

Current local outcome:

- the tracked Lolo replay context, review contract, component-eval contract,
  applicability adjudication, and component adjudication are now in place;
- `compliance-review`, `v1-ea-eval`, and `forest-plan-component-eval` pass for
  `region1-example-lolo-tylers-kitchen-66344`;
- the Lolo slot is now load-bearing in
  `config/forest_plan_component_eval_coverage_v1.json`;
- the downstream blocker chain has since moved the review to
  `source-set-f70ea11e04ae3d53`; and
- `phase-eval` now passes `28/28`; Milestone 3 then used that green runtime
  proof to promote the registry, coverage, and queue surfaces in a verified
  slice.

### Milestone 3 - Registry Promotion, Threshold Ratchet, And Queue Reroute

Outcome label: `resolved`; implemented after the inherited phase-eval blocker
cleared in `e28b373` (`Rebaseline Lolo replay on current source set`).

1. Add a new required review slot to
   `config/v1_real_package_review_coverage_v1.json` for the Lolo review using
   a distinct coverage class such as `forest_specific_reviewer_ready`.
2. Ratchet the real-package coverage manifest so the Lolo slot becomes
   load-bearing:
   - `required_slot_count=4`
   - `required_coverage_class_count=4`
   - `distinct_forest_count_min=3`
   - `reviewer_ready_slot_count_min=3`
3. Update
   `config/forest_specific_example_package_registry_v1.json`:
   - add the new Lolo `review_examples` row
   - switch `lolo-nf` from `profile_eval_guidance_only` to
     `real_package_examples_available`
   - set `primary_example_id`
   - add `FOR-029` to `queue_lineage_source_ids` and
     `queue_boundary_source_ids`
   - ratchet example-lane thresholds so the Lolo example becomes load-bearing:
     `review_example_count_min=4`,
     `reviewer_ready_example_count_min=3`,
     `distinct_governed_example_forest_count_min=3`,
     `profile_guidance_only_count_max=7`
4. Reroute `FOR-029` in
   `config/source_register_queue_resolution_ledger_v1.json` out of
   `promote_direct_file` and into the forest-specific example lane as an
   explicit project-specific boundary row.
5. Update docs and handoff surfaces so the new primary Lolo example is the next
   read for `lolo-nf`.

Current local outcome:

- `config/v1_real_package_review_coverage_v1.json` now requires four slots,
  four coverage classes, three distinct forests, four package styles, and
  three reviewer-ready slots, with the Lolo
  `forest_specific_reviewer_ready` slot load-bearing.
- `config/forest_specific_example_package_registry_v1.json` now carries the
  Lolo review example and routes `lolo-nf` to
  `real_package_examples_available` with
  `primary_example_id="lolo-tylers-kitchen-forest-specific"`.
- `config/source_register_queue_resolution_ledger_v1.json` now resolves
  `FOR-029` as `forest_specific_example_package`.
- `config/gold_coverage_v1.json` and `config/promotion_suite_v1.json` now
  ratchet review-contract diversity to the four-review / three-forest /
  four-package-style Lolo-inclusive floor.

## Required Implementation Artifacts

### Tracked

- `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
- `config/v1_lolo_tylers_kitchen_real_ea_eval.json`
- `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`
- `config/applicability_adjudications/region1-example-lolo-tylers-kitchen-66344.json`
  only if adjudication is required
- `config/forest_plan_component_adjudications/region1-example-lolo-tylers-kitchen-66344.json`
- updates to `config/forest_plan_component_eval_coverage_v1.json`
- updates to `config/forest_specific_example_package_registry_v1.json`
- updates to `config/source_register_queue_resolution_ledger_v1.json`
- focused tests covering the new slot, routing row, and blocked-state
  invariants

### Milestone 3 Tracked Updates

- `config/v1_real_package_review_coverage_v1.json`
- `config/forest_specific_example_package_registry_v1.json` review-example
  roster and `lolo-nf` promotion fields
- `config/gold_coverage_v1.json`
- `config/promotion_suite_v1.json`

### Local Ignored Evidence

- `source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344/`
- `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/package/`
- `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/`
- `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/compliance_review.json`
- `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`
- `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/forest_plan_component_eval_results.json`
- `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`
- refreshed aggregate outputs for:
  `real_package_review_coverage_eval`,
  `forest_plan_component_eval_coverage`, and
  `forest_specific_example_package_eval`

## Required Documentation And Handoff Updates

- `README.md`
- `docs/AGENT_START_HERE.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- this packet

## Required Verification Gates

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344 \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344 \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --forest-unit-id lolo-nf \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-context-build \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --package-path source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-retrieve \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-f70ea11e04ae3d53

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344 \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-f70ea11e04ae3d53 \
  --forest-unit-id lolo-nf \
  --rule-pack source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/generated_rule_pack.json \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --eval-file config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json

# Final review-readiness readback for the current Lolo replay.
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344

PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage \
  --output-dir source_library \
  --manifest config/forest_plan_component_eval_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval \
  --output-dir source_library \
  --manifest config/forest_specific_example_package_registry_v1.json

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx

PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_forest_plan_component_eval_coverage.py \
  tests/test_forest_specific_example_package_registry.py \
  tests/test_forest_specific_example_package_eval.py \
  tests/test_source_register_queue_resolution.py \
  tests/test_cli_eval.py \
  tests/test_architecture_contract.py -q

PYTHONPATH=src .venv/bin/python -m ruff check \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_forest_plan_component_eval_coverage.py \
  tests/test_forest_specific_example_package_registry.py \
  tests/test_forest_specific_example_package_eval.py \
  tests/test_source_register_queue_resolution.py \
  tests/test_cli_eval.py

git diff --check
```

## Acceptance Criteria

- The local Lolo intake path exists and the package authority includes
  `Decision`, `Analysis`, `Consultation`, and `Scoping` inputs.
- The frozen replay context exists and resolves repo-relatively to the local
  intake path and the active source-set baseline.
- `region1-example-lolo-tylers-kitchen-66344` writes and preserves the minimum
  governed artifact floor:
  `package/`, `applicability/applicability_validation.json`,
  `compliance_review.json`, `v1_ea_eval_results.json`,
  `forest_plan_component_eval_results.json`, and `phase_eval_results.json`.
- `v1-ea-eval` reports the Lolo review as `reviewer_ready`, and
  `phase-eval` is green on `source-set-f70ea11e04ae3d53`.
- `config/forest_plan_component_eval_coverage_v1.json` contains a tracked Lolo
  review slot aligned to the current Lolo replay source set. Any aggregate
  coverage red outside the Lolo slot remains visible instead of being papered
  over by this packet.
- `config/forest_specific_example_package_registry_v1.json` routes
  `lolo-nf` as `real_package_examples_available`, records
  `queue_boundary_source_ids=["FOR-029"]`, and points the forest row at
  `lolo-tylers-kitchen-forest-specific`.
- `FOR-029` is no longer a planned direct-file master-promotion row and instead
  resolves explicitly through the forest-specific example lane.
- `FINAL-Q-LOLO-001` remains routed to the separate Lolo Pinyon blocker packet.
- Docs and handoff surfaces point future Lolo example-package readers at this
  packet as the resolved promotion record and route new forest-specific
  example expansion through the umbrella boundary plan.

## Stop Conditions

- Stop if the root Box folder cannot be downloaded completely or cannot preserve
  the `Analysis`, `Consultation`, or `Scoping` specialist/supporting record
  families.
- Stop if `FOR-029` turns out to be shared canonical source input instead of a
  project-specific example boundary; that would require a different workbook and
  queue-governance packet.
- Stop if the Lolo review cannot honestly reach `reviewer_ready` after tracked
  adjudication replay and the remaining blocker is structural; close the packet
  as `reduced` and open a typed-blocked or blocker follow-on instead of
  weakening gates.
- Stop if generic runtime work outside this packet becomes necessary, such as
  broad signer-facing artifact generalization that is not required for the
  minimum forest-specific example floor.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no milestone in this plan is complete until
  verification passes, durable docs and handoff updates land, and the local
  atomic commit exists. A verified but uncommitted slice is only
  ready-to-close.
- Commit Milestone 0 as a docs-and-gate rebaseline slice if it materially
  changes routing or tracked contract shape.
- Commit each later milestone only after its verification gates pass and the
  required docs/handoff updates land in the same slice.
- Stage only the verified Lolo example packet work. Do not stage unrelated
  `source_library/` evidence, unrelated queue rows, or unrelated forest lanes.

## Residual Risks And Next Routing

- The package already uses tracked applicability and component adjudications;
  keep those contracts replayable if a future source-set refresh changes the
  review outputs.
- The current blocker is no longer runtime readiness or Lolo registry
  promotion. The next truthful routing is a new forest-specific example packet
  for another forest, or a separate non-Lolo component-coverage repair packet
  if the request targets that aggregate red.
- Even after this packet closes, other forests remain uncovered. The likely
  next adjacent packets are Helena-Lewis and Clark `Bonanza` and
  Nez Perce-Clearwater `Twentymile`.
- If a future Lolo aggregate gate regresses, open a dedicated Lolo
  typed-blocked or blocker packet rather than silently restoring stale
  `profile_eval_guidance_only` wording.
