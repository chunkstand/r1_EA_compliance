# Idaho Panhandle Lacy Lemoosh Example Package Milestone Plan
Date: 2026-05-29
Status: Active. Milestones 0-1 are resolved locally; Milestone 2 is reduced
only on active-source FEIS readiness.
Plan class: implementation
High-risk implementation: yes
Owner context: standalone follow-on from `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Commit policy: each completed milestone closes only after verification,
affected docs/handoff updates, and a local atomic commit.

## Purpose
Open the governed Idaho Panhandle National Forests Lacy Lemoosh lane without
contaminating `Document_Register_Master` or claiming reviewer-ready status
before deterministic review gates pass.

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

`idaho-panhandle-nfs` remains `profile_eval_guidance_only` until forest-plan
component/adjudication, compliance, V1 eval, phase eval, and promotion gates
pass. Existing Idaho Panhandle queue row `FOR-022` is project `67684`, not Lacy
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
- Milestone 2 resolves scope from package-backed `St. Joe Ranger District`
  evidence, builds `52` components and `8` standards, resolves St. Joe
  Geographic Area, Management Area 6, RHCA, and WUI vocabulary, and completes
  component adjudication for `52/52` reviewer-resolution items. Validation is
  still blocked because FEIS records `R1PLAN-idaho-panhandle-nfs-04`/`-05` have
  zero indexed chunks in `source-set-f70ea11e04ae3d53`.
- District lock: preserve `St. Maries Ranger District` as the project-page/Box
  authority label and `St. Joe Ranger District` as package scope evidence.

## Goal
Create and close a governed Lacy Lemoosh example package lane as the Idaho
Panhandle primary example only after package authority, review artifacts, eval
contracts, and aggregate gates are present and green.

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
- packet: `docs/IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- registry: `config/forest_specific_example_package_registry_v1.json`
- replay context:
  `config/replay_contexts/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`
- future contracts: `config/v1_idaho_panhandle_lacy_lemoosh_real_ea_eval.json`,
  `config/forest_plan_component_evals/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`,
  `config/applicability_adjudications/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`,
  `config/forest_plan_component_adjudications/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`
- aggregate manifests: `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- ignored outputs:
  `source_library/reviews/_intake/region1-example-idaho-panhandle-lacy-lemoosh-60853/`
  and `source_library/reviews/region1-example-idaho-panhandle-lacy-lemoosh-60853/`
- docs and tests:
  `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`,
  `tests/test_forest_specific_example_package_registry.py`

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
### Weak Point 1
Forecast: Lacy Lemoosh is treated as shared master input.
- Owner surface: workbook, `Document_Register_Master`, queue ledger
- Prevention gate:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_specific_example_package_registry.py`
- Fail threshold: any Lacy Lemoosh package row is added to the master table, or
  unrelated Idaho Panhandle queue rows are resolved as this package

### Weak Point 2
Forecast: Idaho Panhandle is promoted from URL or folder inventory
alone.
- Owner surface: registry, real-package coverage, component coverage
- Prevention gate: review `phase-eval`, V1 eval, component eval,
  `real-package-review-coverage-eval`, and `forest-specific-example-package-eval`
- Fail threshold: Idaho Panhandle leaves `profile_eval_guidance_only`, or a
  Lacy slot becomes required reviewer-ready coverage, before package authority
  and review gates pass

### Weak Point 3
Forecast: intake drops `Draft EA` or `Scoping` and reviews only
final decision-core PDFs.
- Owner surface: ignored intake path and replay context
- Prevention gate: package inventory, import manifest, hashes, and `ea-review`
- Fail threshold: intake lacks `Decision`, `Final EA`, `Draft EA`, or
  `Scoping` unless a milestone proves a narrower official replay path

### Weak Point 4
Forecast: scope resolves by broad lexical match without
package-specific evidence.
- Owner surface: forest-plan profile, context summary, component contracts
- Prevention gate: `forest-plan-resolve`, component adjudication eval, and
  forest-plan component eval
- Fail threshold: ambiguous scope, missing required source records, unresolved
  mentions, or pending component queue items remain

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
Outcome label: `reduced`. Scope resolves to `idaho_panhandle_nfs`; review-local
inventory builds `52` components and `8` standards from `FOR-021`; Idaho
profile vocabulary resolves St. Joe Geographic Area, Management Area 6, RHCA,
and WUI context; component adjudication resolves the current `52`
reviewer-resolution items with `0` pending. The remaining blocker is missing
indexed FEIS records `R1PLAN-idaho-panhandle-nfs-04`/`-05` in
`source-set-f70ea11e04ae3d53`. Registry/coverage manifests remain unchanged.

### Milestone 3 - Reviewer Stack Replay
Outcome label: `resolved` if the review reaches reviewer-ready status;
`reduced` if a named applicability, component, compliance, or eval blocker
remains.
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
Milestone 0:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md --strict
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_specific_example_package_registry.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
git diff --check
```

Milestone 1:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review --package-path source_library/reviews/_intake/region1-example-idaho-panhandle-lacy-lemoosh-60853 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-idaho-panhandle-lacy-lemoosh-60853 --docling-timeout-seconds 180
PYTHONPATH=src uv run --extra dev pytest tests/test_replay_context.py tests/test_forest_specific_example_package_registry.py
git diff --check
```

Milestone 2:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library/reviews/region1-example-idaho-panhandle-lacy-lemoosh-60853/component_inventory_build --source-set-id source-set-f70ea11e04ae3d53 --source-record-id FOR-021 --forest-unit-id idaho-panhandle-nfs --plan-version 2015 --chunks-path source_library/derived/source-set-f70ea11e04ae3d53/chunks/chunks.jsonl
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/_intake/region1-example-idaho-panhandle-lacy-lemoosh-60853 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-idaho-panhandle-lacy-lemoosh-60853 --forest-unit-id idaho-panhandle-nfs --forest-plan-component-inventory-path source_library/reviews/region1-example-idaho-panhandle-lacy-lemoosh-60853/component_inventory_build/derived/source-set-f70ea11e04ae3d53/forest_plan_components/component_inventory.json --reuse-package-cache --docling-timeout-seconds 180
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver_scope.py tests/test_forest_specific_example_package_registry.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Milestones 3-4 add matching compliance, V1, component, `phase-eval`,
coverage, architecture, ruff, compile, and `git diff --check` gates.

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

Milestone 0 closeout on 2026-05-29: plan lint passed; registry tests passed
`13/13`; `forest-specific-example-package-eval` and `git diff --check` passed.
Residual risk: package-authority intake remained, with no Lacy slot or primary
example yet.

Milestone 1 closeout on 2026-05-29: Box inventory/download completed with
`186` files, `553,664,116` expected/actual bytes, and `failure_count=0`;
`ea-review` passed with `186/186` extracted files, `7,404` chunks, no package
failures, and `validation_passed=true`; focused replay/registry tests,
aggregate eval, ruff, JSON parse, and `git diff --check` passed.

Milestone 2 closeout on 2026-05-29: profile source IDs were reconciled to
active catalog IDs proven in `config/r1_forest_plan_identity_reconciliation_v1.json`;
package-backed `St. Joe Ranger District` vocabulary was added; review-local
inventory build passed with `52` components and `8` standards; resolver scope
is `idaho_panhandle_nfs` with `unresolved_mention_count=0`; validation is
reduced because `R1PLAN-idaho-panhandle-nfs-04`/`-05` have zero indexed chunks.
Initial local commit: `a1574b3`. Follow-on closeout resolves Idaho area/overlay
vocabulary and component adjudication: `forest-plan-resolve` now reports
`geographic_area_count=1`, `management_area_count=1`, and `overlay_count=2`;
`forest-plan-component-adjudication-eval` passes with `52/52` resolved,
`0` pending, `36` `evidence_linking_miss`, `15`
`applicability_false_positive`, and `1` `component_inventory_overreach`. Idaho
Panhandle still has no Lacy Lemoosh coverage slot or primary example.

## Gap-Close Verification Addendum
Milestones 0-2 are gap-closed only while `CURRENT_ROUTING`, `SESSION_HANDOFF`,
`CURRENT_SYSTEM_STATE`, `AGENT_START_HERE`, README, registry guidance, focused
tests, aggregate eval, resolver outputs, and replay context agree that Lacy
Lemoosh has local package authority, green base review, reduced forest-plan
preflight, and remains unpromoted: `idaho-panhandle-nfs` stays
`profile_eval_guidance_only`, `primary_example_id=null`, and no Lacy coverage
slot exists until FEIS source-delta/retrieval readiness, reviewer-stack, and
promotion gates pass.
