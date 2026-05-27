# Lolo Tyler's Kitchen Example Package Milestone Plan

Date: 2026-05-24
Status: Historical reduced parent packet (`Milestones 0-2 remain preserved as
package-authority and registry closeout context; live contract-blocker work
now routes through
docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`)
Owner context: broader standalone follow-on from
`docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`

## Latest Historical Alignment Note

- This packet no longer owns the live Tyler's Kitchen blocker route. Fresh
  tracked readback now shows that the replay context and tracked `v1-ea-eval`
  contract still point at `source-set-4fb59e9eb43045cb`, the live
  `v1_ea_eval_results.json` reports
  `source-set-5e65d845ce77e1a0` with `contract_status="mismatch"`, and the
  live review `phase-eval` remains red at `12/29` on `4fb...`.
- Live work therefore first continued in
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  but that packet has now reduced further into the exact live owner:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
  which owns the current tracked source-set contract split for the replacement
  candidate.
- This packet now remains as the broader Tyler's Kitchen package-authority,
  queue-boundary, and forest-registry parent record only.

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
  National Forest example-package work while this lane remains
  `profile_eval_guidance_only`;
- `FOR-029` is now truthfully routed as a packet-owned `named_blocker` row
  instead of a planned canonical promotion row;
- packet-local `v1-ea-eval`, `forest-plan-component-eval`, and
  `forest-plan-component-eval-coverage` are green; but
- review-scoped `phase-eval` is still inherited-red on
  `source-set-5e65d845ce77e1a0`, so `lolo-nf` must remain
  `profile_eval_guidance_only` and Milestone 3 promotion stays deferred.

## Current Evidence

- `config/forest_specific_example_package_registry_v1.json` still routes
  `lolo-nf` as `profile_eval_guidance_only`, but the forest row now carries
  `queue_boundary_source_ids=["FOR-029"]` and the guidance note that Tyler's
  Kitchen should be reviewed first as the active Lolo example boundary while
  the profile-eval contract remains the routing floor until the inherited
  `phase-eval` blocker is cleared.
- `source_library/reviews/forest_specific_example_package_eval/forest_specific_example_package_eval_results.json`
  is currently green but still shallow at `review_example_count=3`,
  `reviewer_ready_example_count=2`,
  `distinct_governed_example_forest_count=2`, and
  `profile_guidance_only_count=8`.
- `config/source_register_queue_resolution_ledger_v1.json` now routes
  `FOR-029` (`Tyler's Kitchen Fuels Reduction and Forest Health Project`) to
  this packet as `planned_disposition="named_blocker"` and
  `resolution_status="blocked"` while preserving the workbook-matching queue
  identity text.
- `config/forest_plan_component_eval_coverage_v1.json` now contains a required
  Lolo review slot, and the aggregate replay is green at
  `required_review_count=4`, `covered_review_count=4`, and
  `distinct_forest_count=3`.
- `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`
  is green with `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`, but
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`
  is still red with `missing_direct_eval_phase_count=1` and
  `threshold_failed_phase_count=1`.
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
  `config/forest_plan_component_eval_coverage_v1.json`; but
- `phase-eval` remains inherited-red on missing extraction direct eval coverage
  and retrieval direct-eval threshold failures for
  `source-set-5e65d845ce77e1a0`, so the packet stops here instead of forcing
  Milestone 3 green.

### Milestone 3 - Registry Promotion, Threshold Ratchet, And Queue Reroute

Outcome label: `deferred pending inherited phase-eval blocker`

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

### Intentionally Unchanged Until The Blocker Clears

- `config/v1_real_package_review_coverage_v1.json`
- `config/forest_specific_example_package_registry_v1.json` review-example
  roster and `lolo-nf` promotion fields

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
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344 \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --forest-unit-id lolo-nf \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-context-build \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --package-path source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-retrieve \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path source_library/reviews/_intake/region1-example-lolo-tylers-kitchen-66344 \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-5e65d845ce77e1a0 \
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

# Expected blocker-detection command for the current reduced packet.
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
- `v1-ea-eval` reports the Lolo review as `reviewer_ready`, but
  `phase-eval` stays recorded as the inherited blocker rather than being
  papered over or weakened.
- `config/forest_plan_component_eval_coverage_v1.json` contains a tracked Lolo
  review slot and the aggregate coverage replay passes under the ratcheted
  thresholds.
- `config/forest_specific_example_package_registry_v1.json` still routes
  `lolo-nf` as `profile_eval_guidance_only`, but now records
  `queue_boundary_source_ids=["FOR-029"]` plus the active packet guidance
  note.
- `FOR-029` is no longer a planned direct-file master-promotion row and instead
  routes explicitly through the forest-specific example lane.
- `FINAL-Q-LOLO-001` remains routed to the separate Lolo Pinyon blocker packet.
- Docs and handoff surfaces point future sessions at this Lolo packet as the
  active reduced slice and make the inherited `phase-eval` blocker explicit.

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

- The package may still require tracked applicability adjudications before it
  becomes promotion-ready; that is acceptable only if the adjudication
  contract is explicit and replayable.
- The current blocker is not package-local any more; the next truthful routing
  is a follow-on that repairs extraction/retrieval direct eval readiness for
  the inherited `source-set-5e65d845ce77e1a0` review-scoped `phase-eval`
  contract before reattempting Milestone 3 promotion.
- Even after this packet closes, other forests remain uncovered. The likely
  next adjacent packets are Helena-Lewis and Clark `Bonanza` and
  Nez Perce-Clearwater `Twentymile`.
- If Lolo closes only as `reduced`, the next truthful follow-on is a dedicated
  Lolo typed-blocked or blocker packet rather than silently restoring
  `profile_eval_guidance_only`.
