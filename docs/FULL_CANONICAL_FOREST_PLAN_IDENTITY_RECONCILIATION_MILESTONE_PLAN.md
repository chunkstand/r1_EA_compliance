# Full Canonical Forest Plan Identity Reconciliation Milestone Plan

Date: 2026-05-19
Status: Active 2026-05-19; Milestone 0 resolved 2026-05-19 through `d3606ad`; Milestone 1 next
Owner context: `/Users/chunkstand/projects/usfs-r1-EA-sources` active full-canonical forest-plan identity reconciliation boundary

## Purpose

The prior full-canonical downstream rerun packet is now blocked on a narrower issue than extraction
or source-set freshness: the active canonical source set `source-set-9e7d85759951c279` no longer
contains the legacy `R1PLAN-*` source-record identity family that still drives the forest-plan
inventory, readiness, and retrieval-eval contracts. This packet exists to convert that blocker from
an informal handoff note into governed repo data, then use that data to rebind the forest-plan
contracts onto canonical active-catalog identities before the blocked downstream reruns resume.

## Current Evidence

- `source_library/derived/source-set-9e7d85759951c279/forest_plan_components/summary.json`
  currently records `passed=false`, `component_count=0`, `standard_count=0`, and all `10`
  tracked forests blocked by
  `no_selected_forest_plan_chunks`,
  `plan_component_labels_not_detected`, and
  `plan_standard_labels_not_detected`.
- `config/r1_forest_plan_component_inventory_build_manifest.json` and
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`
  together reference `99` distinct legacy `R1PLAN-*` source-record IDs.
- Against the active canonical catalog in `source_library/catalog/source_catalog.jsonl`, `74` of
  those `99` legacy source-record IDs already have an exact official-URL match to a current
  canonical source-record ID.
- The remaining `25` legacy source-record IDs are not yet governably bound to a current canonical
  source-record ID. `14` remain `source_delta_required`, and `11` are `catalog_confirmed`
  planning or document-set landing pages with no exact current active-catalog row.
- `config/forest_plan_component_retrieval_eval_v1.json`
  still carries legacy component IDs for the retrieval-eval cases, so source-record rebind and
  component-identity rebind must stay sequenced rather than being mixed together.
- The prior packet
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`
  is now reduced through the active-source-set rebind. Its next routing is this dedicated
  identity-reconciliation packet, not another blind downstream rerun attempt.

## Goal

Return the forest-plan downstream lane to a truthful replayable state by:

- materializing the current legacy-to-canonical identity census as governed repo data,
- rebinding the inventory and readiness contracts to canonical source-record IDs where exact URL
  proof already exists,
- isolating the remaining unresolved legacy rows as explicit blocker surfaces instead of hidden
  manifest debt, and
- reopening the path to `forest-plan-components-build`,
  `forest-plan-profile-eval`,
  `forest-plan-component-retrieval-eval`,
  `nepa-knowledge-graph-export`, and
  `promotion-suite`
  on `source-set-9e7d85759951c279`.

## Non-Goals

- Do not claim a green full-canonical corpus in this packet unless the blocked downstream reruns
  actually land.
- Do not guess source-record mappings by title similarity, forest name similarity, or document-role
  intuition when an exact URL-backed mapping is not available.
- Do not hand-edit `source_library/` artifacts or `component_inventory.json` to force a green
  forest-plan inventory.
- Do not silently rewrite retrieval-eval component IDs before a canonical component inventory
  actually exists.
- Do not treat preserved `existing_source_record_id` values in
  `config/r1_forest_plan_document_register_draft.csv`
  as canonical active-catalog bindings when they still point at legacy `R1PLAN-*` identities.

## Scope

- a governed forest-plan identity reconciliation registry artifact
- a reusable generator/loader surface for that registry
- focused tests that prove the registry matches the active manifest/readiness reference set and
  preserves the exact current counts
- durable docs and handoff routing that move the active packet from the reduced downstream rerun
  lane to this dedicated identity-reconciliation lane
- future manifest/readiness/component-eval rebind milestones driven by that registry

## Out Of Scope

- workbook changes
- downloader, catalog, extraction, or currentness changes
- broad multi-forest source-delta capture
- direct downstream reruns while the forest-plan identity contracts are still mixed
- review-ready East Crazies or expansion-slot work

## Owner Surfaces

- `src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py`
- `tests/test_forest_plan_identity_reconciliation.py`
- `config/r1_forest_plan_identity_reconciliation_v1.json`
- `config/r1_forest_plan_component_inventory_build_manifest.json`
- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `config/forest_plan_component_retrieval_eval_v1.json`
- `config/r1_forest_plan_document_register_draft.csv`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`
- `source_library/derived/source-set-9e7d85759951c279/forest_plan_components/summary.json`
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`
- this plan file

## Placement Rules

- Keep the reconciliation artifact in `config/` as governed repo data, not as a handoff-only note.
- Keep reconciliation logic in a dedicated source module. Do not bury it inside inventory-build,
  retrieval-eval, or promotion-suite code before the contract is proven.
- Use exact official-URL matching as the only automatic binding rule in this packet.
- Keep unresolved rows explicit. Do not drop them from the registry just because they cannot be
  rebound yet.
- Sequence source-record identity rebind before retrieval component-identity rebind.
- Keep the active routing set aligned across `README.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`, `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`,
  and this plan file.

## Weak-Point Prevention Contract

### Weak Point 1: a fake canonical mapping slips in without proof

- Weak point forecast: a future session could bind a legacy `R1PLAN-*` row to the wrong canonical
  source-record ID just because the title looks similar.
- Owner surface: reconciliation generator, committed registry, and focused tests.
- Prevention gate: exact-match bindings in the registry must come from one and only one exact
  official-URL match against the active canonical catalog.
- Fail threshold: a bound canonical ID appears without an exact URL match, or a legacy row with
  multiple exact URL matches is silently treated as resolved.
- Controlled violation: unit coverage must include both a single-match success case and an
  unresolved case.
- Future-Codex misuse scenario: mapping Flathead Box-hosted records to canonical IDs by partial
  filename or title because they “look right.” This packet prevents that by making exact-URL proof
  the only automatic route.

### Weak Point 2: unresolved rows disappear from the blocker accounting

- Weak point forecast: manifest rebind work could hide the still-unresolved `25` rows by simply
- removing them from the active accounting surface.
- Owner surface: committed registry, state docs, and future manifest rebind milestone.
- Prevention gate: the registry must enumerate every currently referenced legacy source-record ID
  exactly once as either `exact_url_matched` or `unresolved`.
- Fail threshold: the registry total drifts below `99`, unresolved counts stop matching live
  evidence, or a referenced legacy row is absent from the artifact.
- Controlled violation: a focused contract test recomputes the referenced ID set from the live
  manifest/readiness configs and compares it against the committed registry.
- Future-Codex misuse scenario: deleting the hard rows from the registry to make the remaining
  counts look cleaner. The exact-total gate prevents that.

### Weak Point 3: source-record and component-identity work get conflated

- Weak point forecast: a future session could start rewriting retrieval-eval component IDs before a
  canonical component inventory exists, producing another false green.
- Owner surface: this plan, retrieval-eval config, and future Milestone 2.
- Prevention gate: Milestone 1 may touch only source-record identity surfaces; retrieval component
  IDs stay unchanged until a canonical inventory build succeeds.
- Fail threshold: `config/forest_plan_component_retrieval_eval_v1.json` is rebound to new
  component IDs before a truthful canonical component inventory exists.
- Controlled violation: docs and handoff routing must name retrieval component rebind as a later
  milestone, not a hidden side effect of Milestone 1.
- Future-Codex misuse scenario: patching the eval case IDs first because they are easy to edit.
  The milestone order prevents that shortcut.

### Weak Point 4: the old reduced rerun packet stays marked active

- Weak point forecast: the repo could land the new registry but keep the older full-canonical
  rerun plan marked as the active packet, confusing the next session.
- Owner surface: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`,
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`, and this plan file.
- Prevention gate: closeout requires those docs to agree that this identity-reconciliation packet
  is now the active implementation surface and that the older rerun packet is blocked on it.
- Fail threshold: any active routing doc still says the next step is to rerun downstream artifacts
  directly from the reduced Milestone 3 state.
- Controlled violation: targeted `rg` checks over the active routing set before commit.
- Future-Codex misuse scenario: resuming the old rerun plan and forgetting this packet exists.
  The routing docs must make that impossible.

## Milestone Sequence

### Milestone 0: Rebaseline And Land The Governed Identity Registry

Outcome label: resolved

- Closing commit hash:
  `d3606ad` (`Close identity reconciliation Milestone 0 baseline`)

- Reconfirm the live blocker evidence from:
  `source_library/derived/source-set-9e7d85759951c279/forest_plan_components/summary.json`,
  `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `config/r1_forest_plan_document_register_draft.csv`,
  `source_library/catalog/source_catalog.jsonl`, and
  `source_library/catalog/source_set_manifest.json`.
- Materialize the current identity census as
  `config/r1_forest_plan_identity_reconciliation_v1.json`, with exact URL matches and unresolved
  rows carried as separate explicit sets.
- Add a dedicated generator/loader surface plus focused tests so future sessions can regenerate the
  registry from current repo inputs instead of hand-editing it.
- Closed `2026-05-19` through `d3606ad`: the committed registry now records `99` referenced legacy
  source-record IDs, `74` exact URL-backed canonical bindings, and `25` unresolved rows with
  `unresolved_status_counts={"catalog_confirmed": 11, "source_delta_required": 14}`.

### Milestone 1: Rebind Manifest And Readiness Source-Record IDs

Outcome label: reduced

- Rewrite the source-record identity surfaces in
  `config/r1_forest_plan_component_inventory_build_manifest.json` and
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`
  to use the `74` exact URL-backed canonical source-record IDs from the registry.
- Preserve the unresolved `25` rows as explicit blockers or fallback metadata. Do not silently drop
  them from the active lane.
- Add or update contract tests so the manifest/readiness configs cannot drift back to mixed legacy
  and canonical source-record IDs without failing fast.
- Close the milestone only when the identity mix is reduced to the explicit unresolved set and the
  docs route the next slice to the unresolved blocker family, not to the already-bound rows.

### Milestone 2: Reconcile Retrieval Component Identities

Outcome label: reduced

- After Milestone 1 lands and a truthful canonical component inventory exists again, regenerate the
  forest-plan component inventory on `source-set-9e7d85759951c279`.
- Rebind `config/forest_plan_component_retrieval_eval_v1.json` away from legacy component IDs and
  onto canonical component IDs emitted by that rebuilt inventory.
- Keep the retrieval eval blocked if the canonical component inventory still does not exist.

### Milestone 3: Resume The Blocked Full-Canonical Downstream Reruns

Outcome label: resolved

- Rerun
  `forest-plan-components-build`,
  `forest-plan-profile-eval`,
  `forest-plan-component-retrieval-eval`,
  `nepa-knowledge-graph-export`, and
  `promotion-suite`
  on `source-set-9e7d85759951c279`.
- Close only when the missing/stale full-canonical artifacts regenerate truthfully and promotion no
  longer reports the same forest-plan identity blocker family.

### Milestone 4: Durable Closeout And Routing Reset

Outcome label: resolved

- Update the durable routing set so this packet is either marked resolved or reduced with its exact
- remaining issue named explicitly.
- Record the closeout commit hash and verification commands in `docs/SESSION_HANDOFF.md`.
- If the full-canonical rerun packet becomes active again after Milestone 3, route back to it
  explicitly from this plan.

## Required Implementation Artifacts

- `src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py`
- `tests/test_forest_plan_identity_reconciliation.py`
- `config/r1_forest_plan_identity_reconciliation_v1.json`
- this plan file
- updated routing docs and handoff state

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`
- this plan file

## Required Verification Gates

- Milestone 0 registry gate:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_identity_reconciliation.py -q`
- Source/test lint:
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py tests/test_forest_plan_identity_reconciliation.py`
- Plan lint:
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/FULL_CANONICAL_FOREST_PLAN_IDENTITY_RECONCILIATION_MILESTONE_PLAN.md`
- Docs and closeout:
  `git diff --check`

## Acceptance Criteria

- `config/r1_forest_plan_identity_reconciliation_v1.json` exists and records the active source set
  as `source-set-9e7d85759951c279`.
- The committed registry records `99` referenced legacy source-record IDs, `74` exact URL-backed
  canonical bindings, and `25` unresolved rows.
- The unresolved status split is explicit and preserved at
  `catalog_confirmed=11` and `source_delta_required=14`.
- Focused tests prove the committed registry covers every legacy source-record ID currently
  referenced by the live manifest/readiness pair.
- The active routing set no longer treats the reduced Milestone 3 rerun packet as the active
  implementation surface. This identity-reconciliation packet is now the active packet.

## Stop Conditions

- The live referenced legacy source-record set changes while this packet is being authored, so the
  baseline registry can no longer be trusted without a fresh rebaseline.
- Exact URL matching produces ambiguous multi-row canonical matches that require a governed manual
  adjudication surface before Milestone 1 can continue.
- The next slice would require hand-editing `source_library/` outputs or deleting unresolved rows
  just to make the counts look cleaner.

## Local Commit Closeout Policy

- Implement and close this plan milestone by milestone.
- complete-after-commit rule: no milestone in this plan may be marked complete, `resolved`, or
  `reduced` until verification passes, required docs/handoff updates land, and a local atomic
  commit exists. A verified but uncommitted milestone is ready-to-close, not complete.
- Do not weaken, delete, loosen, or narrow tests just to produce a passing result. If a test or
  gate changes in this packet, the replacement coverage must be equivalent or stronger and must
  make the blocker more explicit rather than easier to bypass.
- Stage only the verified milestone slice.
- Leave unrelated tracked and ignored work alone, including unrelated `source_library/` evidence.
- Include implementation, tests, docs, and handoff updates for the same milestone in the same
  commit.

## Residual Risks And Next Milestone Routing

- The main accepted residual risk after Milestone 0 is that the registry is descriptive, not yet a
  manifest rewrite. That is intentional. The next active slice is Milestone 1 on source-record
  manifest/readiness rebind.
- If a future session cannot prove a canonical binding for one of the `25` unresolved rows, it must
  keep that row explicit as unresolved rather than hiding it inside a broad rerun attempt.
