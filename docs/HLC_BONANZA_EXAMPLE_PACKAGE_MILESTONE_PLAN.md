# HLC Bonanza Example Package Milestone Plan

Date: 2026-05-29
Status: Resolved locally through `Milestone 4` registry and coverage promotion. HLC Bonanza is now
the governed Helena-Lewis and Clark primary example; the standalone component-coverage aggregate
still fails only on the inherited ECID source-delta slot, while the Bonanza component slot and
review-scope promotion gate pass.
Owner context: standalone follow-on from `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`

## Purpose

Open the governed Helena-Lewis and Clark National Forest example-package lane around the user-selected Bonanza EA package without contaminating `Document_Register_Master` or claiming reviewer-ready status before the deterministic review gates pass.

Selected package authority:

- project page: `https://www.fs.usda.gov/r01/helena-lewisclark/projects/66532`
- project title: `Bonanza`
- project ID: `66532`
- public Pinyon/Box folder: `https://usfs-public.app.box.com/v/PinyonPublic/folder/272939272513`
- Box root folder label: `Bonanza (66532)`
- forest: `helena-lewis-and-clark-nf`
- ranger district: `White Sulphur Springs Ranger District`
- expected analysis type: `Environmental Assessment`
- decision signed date: `2025-06-24`
- frozen review ID: `region1-example-helena-lewis-and-clark-bonanza-66532`

## Intent Lock

Bonanza is a Helena-Lewis and Clark forest-specific example. It is not a generic Region 1 example, not a Custer Gallatin substitute, and not evidence that any other forest has a governed real-package example.

The planned governed identity is:

- `example_id="hlc-bonanza-forest-specific"`
- `review_id="region1-example-helena-lewis-and-clark-bonanza-66532"`
- `forest_unit_id="helena-lewis-and-clark-nf"`
- `applicable_forest_unit_ids=["helena-lewis-and-clark-nf"]`
- `coverage_slot_id="hlc-bonanza-forest-specific"`
- `coverage_class_id="forest_specific_reviewer_ready"`
- `queue_lineage_source_ids=[]` unless a later workbook-backed Bonanza queue row is found

HLC remained `profile_eval_guidance_only` in `config/forest_specific_example_package_registry_v1.json` until Bonanza passed package authority, replay context, forest-plan component/adjudication, compliance, V1 eval, phase eval, and the HLC review-scope promotion gates.

## Current Evidence

- `config/forest_specific_example_package_registry_v1.json` now routes `helena-lewis-and-clark-nf` as `real_package_examples_available` with `primary_example_id="hlc-bonanza-forest-specific"`.
- `docs/AGENT_START_HERE.md` now names this packet as the latest resolved
  forest-specific example packet and tells system/agent workflows to inspect
  Bonanza first for HLC example-package work. This is the system-facing HLC
  route; Bonanza must not be reused as generic Region 1 guidance or for any
  non-HLC forest.
- `config/v1_real_package_review_coverage_v1.json` now has the required Bonanza slot `hlc-bonanza-forest-specific`; `real-package-review-coverage-eval` passes with `covered_slot_count=5`, `reviewer_ready_slot_count=5`, `distinct_forest_count=4`, `distinct_package_style_count=6`, and no threshold failures.
- `forest-specific-example-package-eval` passes with `review_example_count=5`, `reviewer_ready_example_count=5`, `distinct_governed_example_forest_count=4`, `profile_guidance_only_count=6`, and no threshold failures.
- `config/forest_plan_component_eval_coverage_v1.json` now includes Bonanza as a required component slot. The standalone aggregate still reports `passed=false` because the inherited `ecid-source-delta-replay` slot is stale/unresolved, but the Bonanza slot passes with `failure_reasons=[]` on `source-set-f70ea11e04ae3d53`.
- The official Box root has been inventoried and downloaded under ignored local evidence at `source_library/reviews/_intake/region1-example-helena-lewis-and-clark-bonanza-66532/`.
- `box_inventory.json` records `5` folders, `47` files, and `65,761,583` expected bytes.
- `box_import_manifest.json` records `47` downloaded files, `65,761,583` actual bytes, and `failure_count=0`.
- `ea-review` on the full Bonanza package passed with `47/47` extracted files, `2,227` package chunks, `package_failed_count=0`, `finding_status_counts={"pass":5}`, `validation_passed=true`, and `reviewer_ready=true`.
- HLC single-forest component inventory was built under the review output tree with `258` components, `28` standards, `coverage_passed=true`, and `component_source_accuracy_passed=true`.
- HLC profile context terms now include `White Sulphur Springs Ranger District` and `Castles Geographic Area`, so Bonanza area evidence resolves without weakening forest-plan validation.
- `forest-plan-component-adjudication-eval` passes for the tracked Bonanza adjudication with `178/178` resolved items, `0` pending items, `disposition_counts={"applicability_false_positive":132,"evidence_linking_miss":46}`, and `failure_category_counts={}`.
- `forest-plan-resolve` on the full package now resolves `scope_status="helena_lewis_and_clark_nf"`, `geographic_area_count=1`, `project_location_signal_count=1`, `validation_passed=true`, and `reviewer_ready=true`; retrieval readiness is green with all required HLC source records indexed on `source-set-f70ea11e04ae3d53`.
- Applicability replay now passes end to end: `applicability-determine` writes `51` applicable
  authorities, `273` non-applicable authorities, and `0` unresolved authorities after the tracked
  five-item adjudication is applied; `applicability-validate` reports
  `generated_rule_pack_ready=true`; and generated rule-pack validation reports `51` rules.
- The tracked applicability adjudication contract is
  `config/applicability_adjudications/region1-example-helena-lewis-and-clark-bonanza-66532.json`.
  It resolves the five authority-family conflicts with `5/5` resolved items, `0` pending items,
  and no failure categories after replay against the regenerated decision hash.
- `compliance-review` on the generated Bonanza rule pack passes with `51` findings,
  `finding_status_counts={"pass":35,"uncertain":16}`, matrix JSON/Markdown/PDF artifacts present,
  `validation_passed=true`, and `reviewer_ready=true`.
- The V1 eval contract at `config/v1_helena_lewis_and_clark_bonanza_real_ea_eval.json` passes with
  `baseline_rule_count=26`, `conditional_expectation_count=25`, `forest_plan_expectation_count=8`,
  `passed=true`, and `contract_status="reviewer_ready"`.
- The component eval contract at
  `config/forest_plan_component_evals/region1-example-helena-lewis-and-clark-bonanza-66532.json`
  passes `28/28` HLC applicable-standard cases with `applicable_standard_recall=1.0` and no failed
  checks.
- Review `phase-eval` now passes `28/28` phases with `blockers=[]`,
  `reviewer_ready=true`, `declared_review_contract=true`, and
  `contract_backed_promotion_ready=true`.

## Goal

Create a governed Bonanza example package lane for HLC, then promote it as the HLC primary example only after deterministic reviewer-stack gates prove it is reviewer-ready.

## Non-Goals

- Do not add Bonanza package files or project-specific rows to `Document_Register_Master`.
- Do not add Bonanza to `config/v1_real_package_review_coverage_v1.json`, `config/forest_specific_example_package_registry_v1.json`, or `config/forest_plan_component_eval_coverage_v1.json` until the review/eval gates pass.
- Do not overwrite the shared f70 Region 1 component inventory just to support HLC. Build HLC component inventory as review-local generated evidence unless a separate Region 1 component-inventory milestone updates the shared inventory.
- Do not weaken forest-plan resolver validation, real-package coverage thresholds, or forest-specific example thresholds to get a green result.
- Do not stage ignored `source_library/` package bytes or generated review outputs unless repo policy changes explicitly.

## Scope

- HLC Bonanza package boundary and review identity
- local ignored package-authority intake and generated review evidence
- tracked replay context for the selected package
- docs and handoff routing to this active packet
- focused tests preserving the HLC no-promotion boundary
- future reviewer-stack and registry promotion only after gates pass

## Out Of Scope

- unrelated HLC projects
- unrelated profile-only forests
- full-canonical source capture or downloader changes
- registry threshold ratchets before Bonanza is reviewer-ready
- global component-inventory promotion unless a later milestone explicitly owns it

## Owner Surfaces

- packet: `docs/HLC_BONANZA_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- replay context: `config/replay_contexts/region1-example-helena-lewis-and-clark-bonanza-66532.json`
- forest-specific umbrella: `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- registry and coverage manifests, when promotion is allowed:
  `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- local ignored intake:
  `source_library/reviews/_intake/region1-example-helena-lewis-and-clark-bonanza-66532/`
- local ignored review outputs:
  `source_library/reviews/region1-example-helena-lewis-and-clark-bonanza-66532/`
- docs:
  `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md`
- tests:
  `tests/test_replay_context.py`, `tests/test_forest_specific_example_package_registry.py`,
  `tests/test_forest_plan_profiles.py`, `tests/test_forest_plan_tracking_profile_eval_fixtures.py`,
  and `tests/test_forest_plan_component_adjudication.py`

## Placement Rules

- Freeze the review slug as `region1-example-helena-lewis-and-clark-bonanza-66532`.
- Keep HLC identifiers forest-qualified; do not use a generic `region1-example-bonanza` review ID.
- Use `source-set-f70ea11e04ae3d53` and the repo-root current catalog for new Bonanza replay context.
- Keep the full Box root as package-authority evidence unless a later milestone proves a narrower replay package is required.
- Keep generated package bytes and review outputs under ignored `source_library/` paths.
- Keep HLC registry status as `profile_eval_guidance_only` until the reviewer-ready promotion milestone passes; after Milestone 4, keep Bonanza as the HLC primary example unless a future gate regresses.

## Weak-Point Prevention Contract

### Weak Point 1

Weak point forecast: Bonanza is promoted from a URL or inventory alone.

- Owner surface: `config/forest_specific_example_package_registry_v1.json`, `config/v1_real_package_review_coverage_v1.json`
- Prevention gate: V1 eval, forest-plan component eval/adjudication, phase eval, real-package coverage eval, and forest-specific example-package eval
- Fail threshold: Bonanza appears as a required active example slot before reviewer-stack gates pass
- Controlled violation: focused registry tests require the HLC Bonanza primary example, coverage
  slot, and component slot to align after the dedicated promotion milestone updates registry and
  coverage manifests
- Future-Codex misuse scenario: a future session edits the registry after seeing the downloaded Box files; the tests and aggregate evals must reject promotion without the eval artifacts

### Weak Point 2

Weak point forecast: the HLC component inventory is hidden in `/tmp` or overwrites the shared f70 Region 1 inventory.

- Owner surface: Bonanza generated review output tree and `forest-plan-resolve` command inputs
- Prevention gate: resolver summary must point to a repo-relative review-local component inventory path, or a separate shared-inventory milestone must own the update
- Fail threshold: resolver evidence references a transient path or shared f70 inventory is overwritten without an explicit milestone
- Controlled violation: rerun `forest-plan-resolve` with a missing component inventory and verify it fails closed
- Future-Codex misuse scenario: a future session gets a green local run from `/tmp` and leaves unreplayable evidence; this packet requires durable review-local generated evidence

### Weak Point 3

Weak point forecast: HLC forest-plan scope is mistaken for reviewer-ready forest-plan compliance.

- Owner surface: `forest_plan_context_summary.json`, component adjudication, and component eval contract
- Prevention gate: forest-plan resolver validation, component adjudication eval, and forest-plan component eval
- Fail threshold: `reviewer_ready=false`, `validation_passed=false`, `adjudication_eval_missing`, unresolved area evidence, or unresolved component queue items remain
- Controlled violation: run `forest-plan-resolve` before adjudication and preserve the typed blocker rather than weakening validation
- Future-Codex misuse scenario: a future session sees `scope_status="helena_lewis_and_clark_nf"` and promotes the package; the plan separates scope resolution from reviewer-ready compliance proof

### Weak Point 4

Weak point forecast: Bonanza contaminates the shared source register.

- Owner surface: active workbook, `Document_Register_Master`, source-register queue ledger, downloader/catalog docs
- Prevention gate: workbook/queue search and source-register queue audit if any queue row is touched
- Fail threshold: Bonanza project package files are added as master-promotion rows without a governed workbook/source-register packet
- Controlled violation: queue tests fail if a non-workbook Bonanza URL is treated as canonical promotion input
- Future-Codex misuse scenario: a later session treats the Box package as downloader input; this packet keeps project-package intake parallel to the master source register

## Milestone Sequence

### Milestone 0 - Open Packet And Freeze Boundary

Outcome label: `resolved`

1. Read current routing, handoff, forest-specific umbrella, registry, and real-package coverage manifests.
2. Freeze the Bonanza review identity and selected official project/documents URLs.
3. Add the tracked replay context only after local package authority exists.
4. Route current docs and handoff to this packet.
5. Verify with focused tests and `git diff --check`.

### Milestone 1 - Local Package Authority Intake

Outcome label: `resolved`

Local result: resolved. The Box root was inventoried and downloaded with hashes. The package has `47` PDFs, `65,761,583` bytes, and `0` download failures. `ea-review` extracted `47/47` files and passed validation.

1. Inventory the official Box root folder and record folder tree, file names, sizes, source folder URLs, and Box IDs.
2. Download visible package documents while preserving folder structure.
3. Hash every local file and record expected vs actual byte counts.
4. Build the first package cache through `ea-review`.
5. Stop as `reduced` if any official documents cannot be inventoried or downloaded completely.

### Milestone 2 - Forest-Plan Resolver Preflight

Outcome label: `resolved`

Local result: resolved. HLC scope resolves, source-record retrieval is ready, Castles area evidence
resolves from package text, component adjudication eval passes, and `forest-plan-resolve` reports
`reviewer_ready=true` for the forest-plan resolver preflight.

1. Build a review-local HLC component inventory from `FOR-018`.
2. Run `forest-plan-resolve` with `--forest-unit-id helena-lewis-and-clark-nf` and the review-local component inventory.
3. Preserve the current blocker if component adjudication or area evidence remains unresolved.
4. Do not change registry or coverage manifests in this milestone.

### Milestone 3 - Reviewer Stack Replay

Outcome label: `resolved` if the Bonanza review reaches reviewer-ready status; `reduced` if a named applicability, component, compliance, or eval blocker remains.

Local result: resolved. Applicability artifacts, the tracked applicability adjudication, generated
rule pack, compliance review matrix/PDF artifacts, V1 eval, forest-plan component eval, and review
`phase-eval` all pass. At this Milestone 3 checkpoint, Bonanza was still outside registry and
coverage promotion surfaces because promotion belonged to Milestone 4.

1. Resolve forest-plan component adjudication for the HLC component queue.
2. Resolve any area/geography validation issue without weakening resolver checks.
3. Run applicability, generated rule-pack, compliance review, V1 eval, forest-plan component eval, and review `phase-eval`.
4. Add tracked eval/adjudication contracts only when generated evidence exists and passes.

### Milestone 4 - Registry And Coverage Promotion

Outcome label: `resolved` for HLC promotion; standalone aggregate component coverage remains
`reduced` by the pre-existing ECID source-delta blocker, not by Bonanza.

Local result: resolved for Bonanza. The real-package and forest-specific aggregate gates are green;
the Bonanza component-coverage slot is required, covered, source-set aligned, and passing; review
`phase-eval` now reports `declared_review_contract=true` and
`contract_backed_promotion_ready=true`. The standalone
`forest-plan-component-eval-coverage` command still exits red because the inherited
`v1-cg-ecid-source-delta-review` slot has `result_not_passed` and
`result_source_set_id_mismatch`.

1. Add Bonanza to `config/v1_real_package_review_coverage_v1.json`.
2. Add Bonanza as the HLC primary example in `config/forest_specific_example_package_registry_v1.json`.
3. Add Bonanza to component-eval coverage only after component eval passes.
4. Rerun real-package coverage eval, forest-specific example-package eval, component-coverage eval, and review `phase-eval`.
5. Update current-state docs and commit the promotion slice atomically.

## Required Verification Gates

Opening/intake slice:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review --package-path source_library/reviews/_intake/region1-example-helena-lewis-and-clark-bonanza-66532 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library/reviews/region1-example-helena-lewis-and-clark-bonanza-66532/component_inventory_build --source-set-id source-set-f70ea11e04ae3d53 --source-record-id FOR-018 --forest-unit-id helena-lewis-and-clark-nf --plan-version 2021 --chunks-path source_library/derived/source-set-f70ea11e04ae3d53/chunks/chunks.jsonl
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/_intake/region1-example-helena-lewis-and-clark-bonanza-66532 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --forest-unit-id helena-lewis-and-clark-nf --forest-plan-component-inventory-path source_library/reviews/region1-example-helena-lewis-and-clark-bonanza-66532/component_inventory_build/derived/source-set-f70ea11e04ae3d53/forest_plan_components/component_inventory.json --reuse-package-cache --docling-timeout-seconds 180
PYTHONPATH=src uv run --extra dev pytest tests/test_replay_context.py tests/test_forest_specific_example_package_registry.py
git diff --check
```

Expected opening result: `ea-review` passes; component inventory build passes; `forest-plan-resolve` may fail closed until component adjudication and area evidence are resolved.

Current forest-plan preflight closeout:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --adjudication-file config/forest_plan_component_adjudications/region1-example-helena-lewis-and-clark-bonanza-66532.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/_intake/region1-example-helena-lewis-and-clark-bonanza-66532 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --forest-unit-id helena-lewis-and-clark-nf --forest-plan-component-inventory-path source_library/reviews/region1-example-helena-lewis-and-clark-bonanza-66532/component_inventory_build/derived/source-set-f70ea11e04ae3d53/forest_plan_components/component_inventory.json --reuse-package-cache --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532
```

Expected current result: adjudication eval passes; `forest-plan-resolve` passes with
`reviewer_ready=true`; the full reviewer stack is now verified in the Milestone 3 closeout gate
below.

Reviewer-stack replay closeout:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-eval --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --adjudication-file config/applicability_adjudications/region1-example-helena-lewis-and-clark-bonanza-66532.json
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-apply --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --source-set-id source-set-f70ea11e04ae3d53 --adjudication-file config/applicability_adjudications/region1-example-helena-lewis-and-clark-bonanza-66532.json
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review --package-path source_library/reviews/_intake/region1-example-helena-lewis-and-clark-bonanza-66532 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --forest-unit-id helena-lewis-and-clark-nf --forest-plan-component-inventory-path source_library/reviews/region1-example-helena-lewis-and-clark-bonanza-66532/component_inventory_build/derived/source-set-f70ea11e04ae3d53/forest_plan_components/component_inventory.json --rule-pack source_library/reviews/region1-example-helena-lewis-and-clark-bonanza-66532/applicability/generated_rule_pack.json --reuse-package-cache --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --eval-file config/v1_helena_lewis_and_clark_bonanza_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --eval-file config/forest_plan_component_evals/region1-example-helena-lewis-and-clark-bonanza-66532.json
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532 --source-set-id source-set-f70ea11e04ae3d53 --validate-only
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-helena-lewis-and-clark-bonanza-66532
PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py -k compliance_review
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Expected reviewer-stack result: generated rule pack and compliance review pass; V1 eval and
component eval pass; review `phase-eval` passes `28/28` with `blockers=[]`; Bonanza remains
unpromoted until Milestone 4.

Promotion slice closeout:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
git diff --check
```

## Acceptance Criteria

- Bonanza has a forest-qualified review ID and replay context on f70.
- Local ignored package evidence records the full official Box roster, file hashes, and zero failures.
- HLC remains profile-guidance-only until the dedicated promotion gates pass, then routes to Bonanza as the governed primary example.
- Forest-plan resolver and reviewer-stack blockers are closed without relaxed validation.
- Any future promotion updates registry, coverage manifests, eval contracts, docs, handoff, and tests in the same milestone commit.

## Stop Conditions

- Official Box files cannot be fully inventoried or downloaded.
- The package resolves to a forest other than HLC.
- Component inventory requires overwriting shared f70 evidence outside this packet.
- Reviewer-ready status requires weakening validation, eval thresholds, or adjudication gates.
- Bonanza appears in active registry/coverage slots before review `phase-eval` and the Bonanza-specific review-scope aggregate gates pass.

## Local Commit Closeout Policy

Each completed milestone slice must be committed atomically with tracked implementation, tests, docs, and handoff updates. Generated `source_library/` evidence remains ignored and should be described in closeout but not staged unless repository policy changes explicitly.

## Gap-Close Verification Addendum

The HLC system route is considered gap-closed only while all of the following
surfaces agree:

- `docs/AGENT_START_HERE.md` names
  `docs/HLC_BONANZA_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` as the latest resolved
  forest-specific example packet and tells HLC workflows to use Bonanza first.
- `config/forest_specific_example_package_registry_v1.json` routes
  `helena-lewis-and-clark-nf` to
  `primary_example_id="hlc-bonanza-forest-specific"`.
- `config/v1_real_package_review_coverage_v1.json` requires the
  `hlc-bonanza-forest-specific` slot as reviewer-ready coverage.
- `config/forest_plan_component_eval_coverage_v1.json` requires the Bonanza
  component-eval slot, and the Bonanza slot passes even if the standalone
  aggregate remains red on the inherited ECID source-delta slot.
- Focused tests must reject stale system-facing routing if the registry and
  agent entrypoint drift apart.

## Residual Risks And Next Routing

HLC Bonanza has no remaining open milestone in this packet. If the next goal is full standalone
component-coverage green, open a separate ECID source-delta/component-coverage repair packet; do
not route that inherited aggregate blocker back into the HLC Bonanza example-package lane.
