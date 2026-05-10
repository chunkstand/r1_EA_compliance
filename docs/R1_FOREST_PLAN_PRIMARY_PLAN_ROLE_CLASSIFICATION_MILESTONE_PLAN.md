# Region 1 Forest-Plan Primary Plan Role Classification Milestone Plan

Date: 2026-05-10

Status: Closed in verified working-tree state; active-source-set manifest refresh still deferred

Owner context: This is a catalog/classification milestone for the Region 1 forest-plan lane. It is
not a parser-expansion milestone, readiness-promotion milestone, or viewer milestone. Its only job
was to ensure the five primary plan PDFs that had been entering the active catalog as
`forest_plan_support` are classified as `forest_plan` so the inventory builder can consume the real
plan documents before later parser and readiness work continues.

## Purpose

The active full-canonical inventory build is blocked for multiple forests because the system is not
feeding the builder the correct primary plan documents under `document_role=forest_plan`.

This milestone exists to close the earlier classification gap first, before trying to solve
legacy-plan parsing or readiness promotion:

- `dakota-prairie-grasslands`
- `flathead-nf`
- `kootenai-nf`
- `lolo-nf`
- `nez-perce-clearwater-nfs`

## Current Implementation Status

Sequences 0 through 3 are implemented in the working tree. The only remaining closeout step inside
this milestone is the atomic commit.

- `catalog.py` no longer treats every `source_input="r1_forest_plan_document_register"` row as
  uniformly `forest_plan_support`.
- The override is manifest-driven from
  `config/r1_forest_plan_component_inventory_build_manifest.json`, not a Python-only allowlist.
- Focused tests in
  [test_catalog.py](/Users/chunkstand/projects/usfs-r1-EA-sources/tests/test_catalog.py) and
  [test_forest_plan_source_delta_readiness.py](/Users/chunkstand/projects/usfs-r1-EA-sources/tests/test_forest_plan_source_delta_readiness.py)
  now prove the five supplemental primary plan rows promote to `forest_plan` while ordinary
  register rows remain `forest_plan_support`.

Sequence 2 is also proven locally, but the proof is split into two surfaces because the tracked
manifest still pins the committed active full-canonical source set:

- live catalog replay under the current uncommitted worktree produced transient active catalog
  `source-set-5e65d845ce77e1a0`
- in that replay, all five target source IDs are `document_role=forest_plan` in
  `source_library/catalog/source_catalog.jsonl`
- the refreshed chunk surface at
  `source_library/derived/source-set-5e65d845ce77e1a0/chunks/chunks.jsonl` now contains
  `document_role=forest_plan` chunks for all five target source IDs, with chunk counts:
  `dakota-prairie-grasslands=2`, `flathead-nf=899`, `kootenai-nf=336`, `lolo-nf=580`,
  `nez-perce-clearwater-nfs=278`
- isolated single-forest inventory runs against those refreshed chunks now prove the builder sees
  the promoted plan bodies:
  `flathead-nf` builds `80` components / `20` standards,
  `kootenai-nf` builds `1` component / `1` standard,
  and the remaining three forests now fail downstream of role classification rather than because the
  primary plan was absent from `document_role=forest_plan`

The manifest-batch replay is not yet refreshed for `source-set-5e65d845ce77e1a0` because
`config/r1_forest_plan_component_inventory_build_manifest.json` remains pinned to committed active
source set `source-set-34061d1e4bf6c460`. That source-set reference refresh is a separate active
catalog promotion step, not part of this classifier milestone.

## Current Evidence

- The tracked build contract in
  [config/r1_forest_plan_component_inventory_build_manifest.json](/Users/chunkstand/projects/usfs-r1-EA-sources/config/r1_forest_plan_component_inventory_build_manifest.json)
  declares these primary plan source IDs:
  - `dakota-prairie-grasslands` -> `R1PLAN-dakota-prairie-grasslands-03`
  - `flathead-nf` -> `R1PLAN-flathead-nf-02`
  - `kootenai-nf` -> `R1PLAN-kootenai-nf-02`
  - `lolo-nf` -> `R1PLAN-lolo-nf-02`
  - `nez-perce-clearwater-nfs` -> `R1PLAN-nez-perce-clearwater-nfs-06`
- The current live local catalog replay is `source-set-5e65d845ce77e1a0`, produced from
  `corpus-update-2026-05-01-cg-support-batches` plus
  `r1-forest-plan-source-delta-capture-20260510-refresh-batches` under the present uncommitted
  worktree.
- In that replay, all five target source IDs now appear in `source_library/catalog/source_catalog.jsonl`
  with `document_role="forest_plan"`.
- Negative control remains intact:
  `R1PLAN-beaverhead-deerlodge-nf-03` still classifies as `forest_plan_support`.
- The role owner remains `_document_role(...)` in
  [catalog.py](/Users/chunkstand/projects/usfs-r1-EA-sources/src/usfs_r1_ea_sources/catalog.py),
  but it now applies a manifest-driven primary-plan override instead of blanket support-only
  classification for register rows.
- The refreshed chunk surface at
  `source_library/derived/source-set-5e65d845ce77e1a0/chunks/chunks.jsonl` now contains
  `document_role=forest_plan` chunks for all five target source IDs with chunk counts:
  `2`, `899`, `336`, `580`, and `278`.
- Isolated downstream proof now confirms the upstream role-classification blocker is removed:
  `flathead-nf` builds `80` components / `20` standards, `kootenai-nf` builds `1` component /
  `1` standard, and the remaining three forests now fail downstream of role classification rather
  than because the primary plan was absent from `document_role=forest_plan`.
- Focused tests that used to lock support-only behavior for all supplemental rows are now updated
  and passing:
  [test_catalog.py](/Users/chunkstand/projects/usfs-r1-EA-sources/tests/test_catalog.py) and
  [test_forest_plan_source_delta_readiness.py](/Users/chunkstand/projects/usfs-r1-EA-sources/tests/test_forest_plan_source_delta_readiness.py).

## Historical Baseline

Before this milestone, the committed active full-canonical source set
`source-set-34061d1e4bf6c460` classified the five target primary plan rows as
`forest_plan_support`, emitted no `forest_plan` chunks for them, and left the inventory builder
starved of the actual plan body. That baseline is now superseded by the working-tree replay
evidence above.

## Goal

Make the five declared primary plan PDFs above classify as `document_role=forest_plan` in the
active catalog and downstream chunk surfaces, while preserving `forest_plan_support` for the rest of
the supplemental Region 1 support-document register.

## Non-Goals

- Do not expand the component parser for legacy uncoded plans in this milestone.
- Do not fix Beaverhead-Deerlodge or Bitterroot component extraction in this milestone.
- Do not promote new readiness statuses into
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` in this milestone.
- Do not change viewer behavior, graph lens defaults, or unrelated NEPA 3D surfaces.
- Do not reclassify all register-sourced PDFs broadly; only the primary plan PDFs proven by the
  build manifest should move to `forest_plan`.

## Scope

In scope:

- catalog role-classification logic for supplemental Region 1 register sources
- the active build-contract linkage from primary plan source IDs to role classification
- focused catalog/readiness tests and targeted downstream forest-plan build proof
- docs and handoff updates that describe the new role-classification rule

Out of scope:

- parser extraction logic for plan component syntax
- readiness/config promotion
- support-document retrieval policy
- unrelated source-delta document-role rewrites

## Owner Surfaces

- [catalog.py](/Users/chunkstand/projects/usfs-r1-EA-sources/src/usfs_r1_ea_sources/catalog.py)
- [test_catalog.py](/Users/chunkstand/projects/usfs-r1-EA-sources/tests/test_catalog.py)
- [test_forest_plan_source_delta_readiness.py](/Users/chunkstand/projects/usfs-r1-EA-sources/tests/test_forest_plan_source_delta_readiness.py)
- [config/r1_forest_plan_component_inventory_build_manifest.json](/Users/chunkstand/projects/usfs-r1-EA-sources/config/r1_forest_plan_component_inventory_build_manifest.json)
- [docs/OUTPUT_SCHEMAS.md](/Users/chunkstand/projects/usfs-r1-EA-sources/docs/OUTPUT_SCHEMAS.md)
- [docs/CURRENT_SYSTEM_STATE.md](/Users/chunkstand/projects/usfs-r1-EA-sources/docs/CURRENT_SYSTEM_STATE.md)
- [docs/SESSION_HANDOFF.md](/Users/chunkstand/projects/usfs-r1-EA-sources/docs/SESSION_HANDOFF.md)
- this plan file

## Placement Rules

- Keep role-classification logic in `catalog.py`; do not bury special cases in the forest-plan
  builder.
- Preserve the build manifest as the authority for which supplemental source record is the primary
  plan. Do not create a second ad hoc allowlist in unrelated modules.
- If a helper is needed, keep it near `_document_role(...)` and make the primary-plan override
  explicit and test-covered.
- Preserve the distinction between `forest_plan` and `forest_plan_support`; this milestone must not
  collapse all supplemental forest-plan documents into one role.

## Weak-Point Prevention Contract

### Weak Point 1: Over-broad reclassification of all register documents

- Weak point forecast: a future Codex session may reclassify every register-sourced PDF from
  `forest_plan_support` to `forest_plan`, which would destroy the support-document boundary.
- Owner surface: `catalog.py`, `test_catalog.py`
- Prevention gate: focused catalog tests proving non-primary supplemental rows remain
  `forest_plan_support`
- Fail threshold: any supplemental register row that is not the manifest-declared primary plan
  changes to `document_role=forest_plan`
- Controlled violation: test fixture where a biological opinion or FEIS row from the register is
  evaluated alongside a primary plan row and must remain `forest_plan_support`
- Future-Codex misuse scenario: "all register rows are forest-plan related, so mark them all
  forest_plan"; this milestone prevents that by making the override depend on explicit primary-plan
  source IDs from the build manifest

### Weak Point 2: Hidden second source of truth for primary plan identity

- Weak point forecast: the implementation could hardcode source IDs in Python instead of deriving
  them from the tracked build contract.
- Owner surface: `catalog.py`, build-manifest loader/config
- Prevention gate: tests that derive the override set from the current manifest and fail if a
  manifest-declared primary plan row is not upgraded
- Fail threshold: code changes are required to add a new forest’s primary plan override after the
  build manifest already declares it
- Controlled violation: fixture with a manifest-declared primary plan row that remains
  `forest_plan_support`, causing the gate to fail
- Future-Codex misuse scenario: adding another literal list of `R1PLAN-*` IDs in a catalog helper;
  this milestone prevents that by requiring manifest-driven derivation

### Weak Point 3: Downstream stale artifacts hide a successful classifier fix

- Weak point forecast: the code may classify correctly in unit tests, but the active catalog/chunk
  surfaces may stay stale and leave the same forest plans blocked.
- Owner surface: catalog-build replay, active catalog artifacts, targeted inventory replay
- Prevention gate: targeted catalog/downstream replay proving the five primary plan source IDs
  become `forest_plan` in the active catalog and appear as `document_role=forest_plan` in the
  resulting chunk surface
- Fail threshold: any of the five primary plan source IDs remain `forest_plan_support` after the
  replay, or still have no `forest_plan` chunks in the rebuilt active source set
- Controlled violation: baseline check on current artifacts should fail before the implementation
- Future-Codex misuse scenario: claiming the fix is done after unit tests only; this milestone
  prevents that by requiring live artifact verification

## Milestone Sequence

### Sequence 0 - Install The Role-Classification Gate

Goal: make the primary-plan misclassification executable before changing classifier logic.

Implementation tasks:

- Add a focused failing or baseline gate that checks the five manifest-declared primary plan source
  IDs above and proves they are currently classified as `forest_plan_support` in the active catalog.
- Add a negative control proving ordinary supplemental support rows remain `forest_plan_support`.
- Document the exact primary-plan override boundary in this plan and the handoff.

Acceptance signals:

- There is a test or executable check that fails when a manifest-declared primary plan row remains
  `forest_plan_support`.
- There is a test or executable check that fails if ordinary supplemental support rows are promoted
  accidentally.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- The active build manifest cannot be used to derive the primary-plan override set cleanly.

### Sequence 1 - Implement Manifest-Driven Primary Plan Role Override

Goal: classify only the five declared primary plan PDFs as `forest_plan`.

Implementation tasks:

- Update `catalog.py` so `source_input="r1_forest_plan_document_register"` is no longer treated as
  uniformly `forest_plan_support`.
- Derive the override set from the current Region 1 inventory build manifest’s
  `primary_plan_source_record_id` values, not from a hardcoded Python list.
- Preserve `forest_plan_support` for the remaining register rows.
- Update focused tests accordingly.

Acceptance signals:

- The five primary plan source IDs classify as `forest_plan`.
- Non-primary register rows still classify as `forest_plan_support`.
- The change is driven by tracked config, not an ad hoc Python-only allowlist.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_forest_plan_source_delta_readiness.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Stop conditions:

- The only way to implement the override is by broadening all register documents to `forest_plan`.
- The manifest cannot be loaded safely from the catalog path without creating a circular dependency
  or hidden runtime coupling.

### Sequence 2 - Replay The Active Catalog And Prove Downstream Surface Alignment

Goal: prove the classifier fix changes the active source-set artifacts, not just test fixtures.

Implementation tasks:

- Rebuild the active catalog with the current canonical/source-delta batch inputs.
- Confirm the five primary plan source IDs now appear in `source_library/catalog/source_catalog.jsonl`
  with `document_role=forest_plan`.
- Regenerate the active extraction/chunk surface if needed and confirm those five primary plan source
  IDs now produce `document_role=forest_plan` chunks.
- Rerun the active inventory build to confirm the upstream role-classification blocker is removed for
  these five forests, even if later parser blockers remain.

Acceptance signals:

- All five primary plan source IDs are `forest_plan` in the active catalog.
- The active chunk surface includes `document_role=forest_plan` chunks for those same source IDs.
- The next blocked signal, if any, is downstream of role classification rather than absence of
  `forest_plan` chunks.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --output-dir source_library --batch-run-id corpus-update-2026-05-01-cg-support-batches --batch-run-id r1-forest-plan-source-delta-capture-20260510-refresh-batches
PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory --output-dir source_library --source-set-id <replayed source_set_id>
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build --output-dir source_library --reuse-existing --reuse-inventory-path source_library/derived/<replayed source_set_id>/reuse_inventory/reuse_inventory.json
# If the replayed source_set_id still matches the tracked manifest reference, rerun the manifest batch build.
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id <replayed source_set_id> --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json
# Otherwise, use isolated single-forest runs against the refreshed chunks to prove the builder now sees the primary plan body.
git diff --check
```

Stop conditions:

- The active catalog replay cannot be reproduced from tracked batch inputs.
- The five source IDs still fail to produce `forest_plan` chunks after replay.
- The replayed active source set diverges from the tracked manifest reference and the task is
  expanded into a broader active-source-set promotion instead of staying role-classification scoped.

### Sequence 3 - Docs, Handoff, And Closeout

Goal: record the new role-classification rule and route the next milestone correctly.

Implementation tasks:

- Update this plan with implementation closeout evidence.
- Update `docs/CURRENT_SYSTEM_STATE.md`, `docs/OUTPUT_SCHEMAS.md`, and `docs/SESSION_HANDOFF.md`
  to describe the new primary-plan override rule and the downstream status after replay.
- Route the next milestone explicitly:
  parser expansion for the now-visible primary plan texts, not another catalog role fix.

Acceptance signals:

- Docs no longer describe the five primary plans as `forest_plan_support` when current artifacts say
  otherwise.
- The handoff names the remaining parser/readiness blockers separately from the now-closed
  role-classification gap.

Required verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/R1_FOREST_PLAN_PRIMARY_PLAN_ROLE_CLASSIFICATION_MILESTONE_PLAN.md --strict
git diff --check
```

Stop conditions:

- Docs or handoff still route the next work to generic role-classification cleanup after this
  milestone is closed.

## Required Implementation Artifacts

- manifest-driven primary-plan role-classification gate
- updated catalog classifier logic
- focused catalog/readiness tests for positive and negative role behavior
- refreshed active catalog artifacts proving the five source IDs now classify as `forest_plan`
- refreshed active chunk/build evidence proving the builder now sees those primary plans as
  `forest_plan` inputs

## Required Documentation And Handoff Updates

- this plan
- [docs/CURRENT_SYSTEM_STATE.md](/Users/chunkstand/projects/usfs-r1-EA-sources/docs/CURRENT_SYSTEM_STATE.md)
- [docs/OUTPUT_SCHEMAS.md](/Users/chunkstand/projects/usfs-r1-EA-sources/docs/OUTPUT_SCHEMAS.md)
- [docs/SESSION_HANDOFF.md](/Users/chunkstand/projects/usfs-r1-EA-sources/docs/SESSION_HANDOFF.md)

## Required Verification Gates

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_forest_plan_source_delta_readiness.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/R1_FOREST_PLAN_PRIMARY_PLAN_ROLE_CLASSIFICATION_MILESTONE_PLAN.md --strict
git diff --check
```

Operational closeout now includes the live active-catalog replay and the follow-on downstream proof
captured above. The remaining closeout action is to land the verified slice as one atomic milestone
commit without mixing the unrelated viewer lane.

## Acceptance Criteria

- The five manifest-declared primary plan source IDs now classify as `forest_plan` in the active
  catalog.
- Non-primary supplemental register rows remain `forest_plan_support`.
- The primary-plan override is derived from tracked build-manifest inputs rather than a hidden
  Python-only list.
- Active chunk artifacts contain `document_role=forest_plan` rows for those five primary plan PDFs.
- The next blocker for those forests, if any, is parser/readiness logic rather than upstream role
  classification.
- Docs and handoff route the next work to parser expansion or readiness promotion instead of another
  broad role cleanup.

## Stop Conditions

- The change would require reclassifying all supplemental forest-plan register rows as
  `forest_plan`.
- The manifest-driven override cannot be implemented without an unsafe hidden dependency or circular
  import.
- Active replay still fails to produce `forest_plan` chunks for the five primary plan source IDs.

## Local Commit Closeout Policy

Close each completed sequence with one local atomic commit only after that sequence’s verification
passes and the affected docs/handoff are aligned. Stage only the verified role-classification slice.
Leave unrelated existing worktree changes alone, including the current viewer-default edits in
`viewer/nepa-3d/app.js` and `tests/test_nepa_3d_viewer.py`, plus unrelated root-level
`East_Crazies_*` draft outputs.

Do not batch this milestone together with parser-expansion or readiness-promotion changes.

Current closeout status: implementation, alignment, and milestone commit are complete once this
verified slice is staged and landed without the unrelated viewer lane.

## Residual Risks And Next Milestone Routing

Even after this milestone closes, the five forests may still fail component extraction because their
plan syntax may not match the current parser. That is expected. This milestone only removes the
upstream role-classification blocker.

After this milestone, the next lane should be:

- parser expansion for legacy or non-2012-rule plan formats now exposed as `forest_plan` inputs; or
- active-source-set manifest/reference refresh if the user explicitly wants the transient replayed
  active catalog promoted before parser work continues.

## Closeout Checklist

- [x] Sequence 0 gate added and failing/baselined
- [x] Sequence 1 classifier change implemented and tested
- [x] Sequence 2 active replay proves the five source IDs become `forest_plan`
- [x] Docs and handoff updated
- [x] Plan linter passes
- [x] Verification gates pass
- [x] Local atomic commit created for the milestone slice
