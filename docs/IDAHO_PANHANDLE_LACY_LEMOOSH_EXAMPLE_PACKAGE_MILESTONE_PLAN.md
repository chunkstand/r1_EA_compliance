# Idaho Panhandle Lacy Lemoosh Example Package Milestone Plan
Date: 2026-05-29
Status: Active. Milestones 0-3 are resolved locally; Milestone 2 FEIS
source-readiness is closed locally in commit `ba3718b`, the current component
adjudication refresh is closed against the live `36`-item queue, and Milestone
3 reviewer-stack replay now passes in commit `3cea9fe`. Milestone 4 registry
and aggregate coverage promotion is next.
Plan class: implementation
High-risk implementation: yes
Owner context: standalone follow-on from `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Commit policy: each completed milestone closes only after verification,
affected docs/handoff updates, and a local atomic commit.

## Purpose
Open the governed Idaho Panhandle Lacy Lemoosh lane without contaminating
`Document_Register_Master` or claiming readiness before deterministic gates pass.

Authority: project page
`https://www.fs.usda.gov/r01/idahopanhandle/projects/60853`, public Pinyon/Box
folder `https://usfs-public.app.box.com/v/PinyonPublic/folder/158229569265`,
project-page lead unit `St. Maries Ranger District`, completed EA decision
signed `2025-05-22`, package scope term `St. Joe Ranger District`, and frozen
review ID `region1-example-idaho-panhandle-lacy-lemoosh-60853`.

## Intent Lock
Lacy Lemoosh is an Idaho Panhandle National Forests example candidate. It is
not a generic Region 1 example, not a substitute for Kootenai or Nez
Perce-Clearwater work, and not evidence that any other forest has a governed
real-package example.

Governed identity:
- `example_id="ipnf-lacy-lemoosh-forest-specific"`
- `review_id="region1-example-idaho-panhandle-lacy-lemoosh-60853"`
- `forest_unit_id="idaho-panhandle-nfs"`
- `applicable_forest_unit_ids=["idaho-panhandle-nfs"]`
- `coverage_slot_id="ipnf-lacy-lemoosh-forest-specific"`
- `coverage_class_id="forest_specific_reviewer_ready"`
- `queue_lineage_source_ids=[]` unless a later workbook-backed Lacy Lemoosh
  queue row is found

`idaho-panhandle-nfs` remains `profile_eval_guidance_only` until compliance,
V1 eval, review `phase-eval`, aggregate coverage, and promotion gates pass.
Existing Idaho Panhandle queue row `FOR-022` is project `67684`, not Lacy
Lemoosh `60853`.

## Evidence
- Live Forest Service and Box readback on 2026-05-29 identify `60853`
  as completed EA work under Idaho Panhandle National Forests, decision
  date `2025-05-22`, `186` listed Box files, and `555,066,969` top-level bytes.
- Local ignored authority records `29` folder pages, `186` files,
  `553,664,116` expected/actual bytes, and `failure_count=0`; the tracked
  replay context binds this package to `source-set-f70ea11e04ae3d53`.
- `ea-review` passes with `186/186` extracted files, `7,404` chunks,
  `package_failed_count=0`, `reviewer_ready=true`, and `validation_passed=true`.
- Registry status remains `profile_eval_guidance_only`, `primary_example_id=null`,
  with no Lacy Lemoosh coverage slot.
- Milestone 2 resolves `St. Joe Ranger District` scope, builds `52` components
  and `8` standards, indexes FEIS records `R1PLAN-idaho-panhandle-nfs-04`/`-05`,
  and closes the current `36`-item component queue with no pending items.
- Milestone 3 resolves the reviewer stack: applicability closes `9/9`, rule
  generation emits `56` rules, compliance/V1/component evals pass, and review
  `phase-eval` passes `28/28`.
- District lock: preserve `St. Maries Ranger District` as the project-page/Box
  authority label and `St. Joe Ranger District` as package scope evidence.

## Goal
Close Lacy Lemoosh as the Idaho Panhandle primary example only after package
authority, review artifacts, eval contracts, and aggregate gates are green.

## Non-Goals
- Do not add Lacy Lemoosh package files or project-specific rows to
  `Document_Register_Master`.
- Do not promote Idaho Panhandle to `real_package_examples_available` before
  forest-plan resolver, `v1-ea-eval`, forest-plan component eval, and review
  `phase-eval` pass.
- Do not reroute unrelated Idaho Panhandle queue rows such as `FOR-020` or
  `FOR-022`.
- Do not ratchet aggregate thresholds in Milestone 0.
- Do not weaken tests, eval thresholds, validation checks, or package/component
  coverage to make the packet green.
- Do not stage ignored `source_library/` evidence unless repo policy changes.

## Scope
- Idaho Panhandle Lacy Lemoosh package boundary and review identity
- packet routing, registry guidance, current-state docs, and handoff
- future replay, review eval, applicability adjudication, forest-plan
  component eval, and aggregate coverage contracts
- registry and coverage promotion only after review-readiness gates pass

## Owner Surfaces
- Packet/docs: this plan, `README.md`, `docs/AGENT_START_HERE.md`,
  `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/SESSION_HANDOFF.md`.
- Registry/coverage: `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`, and
  `config/forest_plan_component_eval_coverage_v1.json`.
- Replay/eval contracts: replay context, V1 eval, component eval, applicability
  adjudication, and component adjudication for
  `region1-example-idaho-panhandle-lacy-lemoosh-60853`.
- Ignored evidence: local intake and review outputs under `source_library/`.
- Tests: `tests/test_forest_specific_example_package_registry.py` and
  `tests/test_idaho_panhandle_lacy_contracts.py`.

## Intent Hierarchy
- Invariant: Lacy Lemoosh is only for `idaho-panhandle-nfs` and remains outside
  `Document_Register_Master` unless a separate source-register packet proves
  shared-source promotion.
- Optimization target: keep packet, registry guidance, current routing, tests,
  and handoff aligned on the same forest-qualified identity before intake.
- Acceptable tradeoffs: generated `source_library/` evidence can remain local
  and ignored; Idaho Panhandle can remain profile-guidance-only while open.
- Non-negotiables: do not weaken tests, lower eval thresholds, mark unrelated
  Idaho Panhandle queue rows as Lacy lineage, or reuse the package for another
  forest.

## Weak-Point Contract
- Shared-master contamination: workbook, `Document_Register_Master`, and queue
  ledger stay untouched; registry tests fail if Lacy rows enter the master table
  or unrelated Idaho Panhandle rows become Lacy lineage.
- Premature promotion: registry and aggregate coverage stay guidance-only until
  review `phase-eval`, V1 eval, component eval, real-package coverage, and
  forest-specific registry eval pass.
- Incomplete intake: package inventory, import manifest, hashes, and `ea-review`
  must retain `Decision`, `Final EA`, `Draft EA`, and `Scoping` unless a later
  milestone proves a narrower official replay path.
- Weak scope resolution: `forest-plan-resolve`, component adjudication eval, and
  component eval must close ambiguous scope, missing required source records,
  unresolved mentions, and pending component queue items.

## Milestone Sequence
### Milestone 0 - Open Packet And Freeze Boundary
Outcome label: `resolved`
1. Verify official project and Box root metadata.
2. Freeze the forest-qualified review identity and package URLs.
3. Add this plan and route docs/handoff to it as the active packet.
4. Keep the registry row `profile_eval_guidance_only` and unpromoted.
5. Verify focused tests, aggregate eval, plan lint, and `git diff --check`.

### Milestone 1 - Local Package Authority Intake
Outcome label: `resolved` locally. The full root inventories and downloads with
zero failures, the replay context is tracked, and base `ea-review` passes.
Inventory the Box root, preserve folder structure, hash downloaded files, add
the replay context after local authority exists, and run `ea-review` on
`source-set-f70ea11e04ae3d53`.

Closeout evidence: ignored intake and tracked replay context exist; manifest
has `file_count=186`, `folder_count=29`, `failure_count=0`,
`actual_total_byte_size=553,664,116`; base review has `package_extracted_count=186`,
`package_chunk_count=7,404`, `package_failed_count=0`, `reviewer_ready=true`,
and `validation_passed=true`. Next route: Milestone 2 forest-plan resolver
preflight; do not promote Idaho Panhandle before Milestones 2-4 pass.

### Milestone 2 - Forest-Plan Resolver Preflight
Outcome label: `resolved` locally. Scope resolves to `idaho_panhandle_nfs`;
review-local inventory builds `52` components and `8` standards from `FOR-021`;
Idaho profile vocabulary resolves St. Joe Geographic Area, Management Area 6,
RHCA, and WUI context; FEIS source-readiness is closed in the local f70
catalog/retrieval surface. Retrieval indexes `R1PLAN-idaho-panhandle-nfs-04`
with `1,606` chunks and `R1PLAN-idaho-panhandle-nfs-05` with `991` chunks, and
`forest-plan-resolve` reports `blocking_missing_source_record_ids=[]`,
component adjudication `reviewer_ready=true`, overall `reviewer_ready=true`,
and `validation_passed=true`. Current component findings remain `16` supported
and `36` gaps, with `8` applicable standards and `3` applied standards, but
the refreshed `36`-item adjudication closes the queue as system misses with
`0` pending items and no expectation mismatches. Registry/coverage manifests
remain unpromoted.

### Milestone 3 - Reviewer Stack Replay
Outcome label: `resolved` locally. Applicability, generated rule-pack,
compliance review, V1 eval, forest-plan component eval, and review
`phase-eval` pass; registry and aggregate coverage promotion remain Milestone 4.
Run applicability, generated rule-pack, compliance review, V1 eval,
forest-plan component eval, and review `phase-eval`. Add tracked
eval/adjudication contracts only when generated evidence exists and passes.

### Milestone 4 - Registry And Coverage Promotion
Outcome label: `resolved` for Idaho Panhandle promotion; `reduced` if a
pre-existing aggregate blocker remains outside the Lacy slot.
Add Lacy Lemoosh to real-package coverage, forest-specific registry, and
component-eval coverage only after reviewer-stack gates pass, then rerun the
aggregate gates and update docs/handoff before committing.

## Required Verification Gates
Use the milestone-appropriate subset of these gates:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md --strict
PYTHONPATH=src uv run --extra dev pytest tests/test_idaho_panhandle_lacy_contracts.py tests/test_forest_specific_example_package_registry.py
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review --package-path source_library/reviews/_intake/region1-example-idaho-panhandle-lacy-lemoosh-60853 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-idaho-panhandle-lacy-lemoosh-60853 --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/_intake/region1-example-idaho-panhandle-lacy-lemoosh-60853 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-idaho-panhandle-lacy-lemoosh-60853 --forest-unit-id idaho-panhandle-nfs --forest-plan-component-inventory-path source_library/reviews/region1-example-idaho-panhandle-lacy-lemoosh-60853/component_inventory_build/derived/source-set-f70ea11e04ae3d53/forest_plan_components/component_inventory.json --reuse-package-cache --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id region1-example-idaho-panhandle-lacy-lemoosh-60853 --adjudication-file config/forest_plan_component_adjudications/region1-example-idaho-panhandle-lacy-lemoosh-60853.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-idaho-panhandle-lacy-lemoosh-60853
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
git diff --check
```

Milestones 3-4 add matching applicability, generated rule-pack, compliance,
V1, component, coverage, architecture, ruff, and compile gates when those
surfaces change.

## Acceptance Criteria
- Lacy Lemoosh has a forest-qualified packet, review ID, and planned example
  identity.
- Idaho Panhandle remains `profile_eval_guidance_only` until promotion gates
  pass.
- Intake records the full official Box roster, hashes, and zero failures before
  replay context is authoritative.
- Forest-plan and reviewer-stack blockers close without relaxed validation.
- Any future promotion updates registry, coverage manifests, eval contracts,
  docs, handoff, and tests in one milestone commit.

## Stop Conditions
- Official Box files cannot be fully inventoried or downloaded.
- The package resolves to a forest other than Idaho Panhandle National Forests.
- Component inventory requires overwriting shared f70 evidence outside this
  packet.
- Reviewer-ready status requires weakening validation, eval thresholds, or
  adjudication gates.
- Lacy Lemoosh appears in registry/coverage slots before review `phase-eval`
  and review-scope aggregate gates pass.

## Closeout Outcome Record
Record each closed milestone with commands run, pass/fail status, skipped
gates, residual risks, docs/handoff updates, and local commit hash.

| Milestone | Closeout evidence |
| --- | --- |
| `0` | 2026-05-29: plan lint, registry tests `13/13`, forest-specific aggregate eval, and `git diff --check` passed; no Lacy slot or primary example yet. |
| `1` | 2026-05-29: Box intake recorded `186` files, `553,664,116` bytes, and `failure_count=0`; `ea-review` passed with `186/186` extracted files, `7,404` chunks, and `validation_passed=true`. |
| `2` initial | 2026-05-29 commit `a1574b3`: source IDs, `St. Joe Ranger District` scope vocabulary, and `52`-component inventory landed; validation was reduced because FEIS records had zero indexed chunks. |
| `2` FEIS | 2026-05-29 commit `ba3718b`: local f70 overlays for `R1PLAN-idaho-panhandle-nfs-04`/`-05` passed extraction/retrieval with `719` sources, `707` artifacts, `11` overlays, `113,830` chunks, and no missing source records. |
| `2` adjudication | 2026-05-30: current `36`-item component queue passes with `36/36` resolved, `0` pending, `real_ea_omission_count=0`, and `forest-plan-resolve` `reviewer_ready=true`. |
| `3` | 2026-05-30 commit `3cea9fe`: applicability resolves `9/9`; rule pack has `56` rules; compliance, V1 eval, component eval `52/52`, and review `phase-eval` `28/28` pass. Residual risk is only Milestone 4 promotion: `contract_backed_promotion_ready=false`, `profile_eval_guidance_only`, and `primary_example_id=null`. |

## Gap-Close Verification Addendum
Milestones 0-3 are gap-closed only while routing docs, handoff, README,
registry guidance, focused tests, aggregate eval, resolver outputs, and replay
context agree that Lacy has local authority, green base review, resolved
forest-plan preflight, green reviewer-stack replay, and remains unpromoted:
`idaho-panhandle-nfs` stays `profile_eval_guidance_only`,
`primary_example_id=null`, and no Lacy coverage slot exists until Milestone 4
promotion gates pass.
