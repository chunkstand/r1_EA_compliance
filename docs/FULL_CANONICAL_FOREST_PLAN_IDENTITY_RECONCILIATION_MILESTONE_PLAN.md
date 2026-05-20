# Full Canonical Forest Plan Identity Reconciliation Milestone Plan

Date: 2026-05-19
Status: Resolved 2026-05-19; Milestone 0 resolved 2026-05-19 through `d3606ad`; Milestone 1 reduced 2026-05-19 through `7dd4fb5`; archived full-canonical source-set refresh/rebind now emits `source-set-732a5a91d31736f8`; Milestone 2 is resolved locally; Milestone 3 is reduced historical runtime context; Milestone 4 is resolved 2026-05-19 through `237c45d`; Milestone 5 is resolved 2026-05-19 through `df2bd28`; live full-canonical follow-on now routes through `docs/FULL_CANONICAL_LIVE_SOURCE_SET_PROMOTION_MILESTONE_PLAN.md`, with Milestone 1 resolved through `09a85f7`
Owner context: `/Users/chunkstand/projects/usfs-r1-EA-sources` active full-canonical forest-plan identity reconciliation boundary

## Purpose

Historical routing note: this packet is locally resolved on the archived
full-canonical boundary. After live-promotion Milestone 1 closeout `09a85f7`,
it remains the source of truth for archived downstream green evidence, but it
is no longer the active live-promotion packet.

The prior full-canonical downstream rerun packet was blocked on a narrower issue than extraction:
the active canonical import source set `source-set-9e7d85759951c279` no longer contained the
legacy `R1PLAN-*` source-record identity family that still drove the forest-plan inventory,
readiness, and retrieval-eval contracts. This packet converted that blocker into governed repo data,
rebound the forest-plan contract surfaces, and now carries the refreshed archived full-canonical
replay boundary that downstream reruns must use.

## Current Evidence

- Archived full-canonical classifier-refresh gate
  `source_library/runs/phase2-canonical-full-canonical-classifier-refresh-20260519/catalog_gate/`
  now emits refreshed full-canonical source set
  `source-set-732a5a91d31736f8`.
- `source_library/derived/source-set-732a5a91d31736f8/forest_plan_components/summary.json`
  now records `passed=true`, `component_count=1416`, `standard_count=397`, and
  `blocked_forest_unit_ids=[]`, `coverage_passed=true`, and
  `component_source_accuracy_passed=true`.
- `source_library/derived/source-set-732a5a91d31736f8/authority_currentness/authority_currentness_report.json`
  now passes with
  `authority_family_count=454`,
  `catalog_source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`,
  `source_currentness_record_count=634`, and
  `validation_passed=true`.
- `source_library/evaluations/forest_plan_profile/forest_plan_profile_eval_results.json`
  now passes with
  `active_source_set_ids=["source-set-732a5a91d31736f8"]`,
  `covered_profile_count=10`, and `profile_failure_count=0`.
- `config/r1_forest_plan_component_inventory_build_manifest.json` and
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`
  now reduce the source-record identity mix to `74` exact canonical
  source-record IDs plus `1` governed catalog rebound and the explicit
  unresolved `24`-row legacy blocker set recorded in
  `config/r1_forest_plan_identity_reconciliation_v1.json`.
- Against the active canonical catalog in `source_library/catalog/source_catalog.jsonl`, `74` of
  those `99` legacy source-record IDs already have an exact official-URL match to a current
  canonical source-record ID, and `1` additional Flathead primary-plan row now has a governed
  catalog rebound from `R1PLAN-flathead-nf-02` to `FINAL-FLAT-001`.
- The remaining `24` legacy source-record IDs are not yet governably bound to a current canonical
  source-record ID. `13` remain `source_delta_required`, and `11` are `catalog_confirmed`
  planning or document-set landing pages with no exact current active-catalog row.
- Both configs now carry committed top-level and per-profile `identity_reconciliation` metadata so
  the unresolved blocker family stays explicit instead of hiding inside a mixed-ID manifest.
- `docs/R1_FOREST_PLAN_PRIMARY_PLAN_ROLE_CLASSIFICATION_MILESTONE_PLAN.md` is now resolved in
  practice as well as code. The refreshed archived replay on
  `source-set-732a5a91d31736f8` now proves the classifier fix all the way through the
  full-canonical component inventory boundary for `10/10` forests.
- `config/forest_plan_profiles.json` now aligns the Flathead active plan and
  supporting primary-plan role to `FINAL-FLAT-001`.
- `config/forest_plan_component_retrieval_eval_v1.json`
  now carries canonical component IDs for the retrieval-eval cases, and
  `forest-plan-component-retrieval-eval` now passes `6/6`.
- The workbook direct-document repair slice is now closed: `WILD-ESA-075` and
  `LEX-USFS-002`, `LEX-USFS-003`, `LEX-USFS-007`, `LEX-USFS-008`,
  `LEX-USFS-011`, `LEX-USFS-012`, `LEX-USFS-013`, `LEX-USFS-016`, and
  `LEX-USFS-017` now point at direct official PDFs in the workbook contract,
  `FPS-420` now admits through ZIP metadata extraction, and download reuse no
  longer accepts stale HTML artifacts when a row now governs a direct PDF.
- `extraction-accuracy-audit` now passes on
  `source-set-732a5a91d31736f8` with `audited_record_count=343`,
  `knowledge_base_admitted_source_record_ids=343`, and
  `knowledge_base_blocked_source_record_ids=0`.
- The downstream archived replay chain is now green on
  `source-set-732a5a91d31736f8`: `retrieval-build` is reviewer-ready with
  `chunk_count=98699`; `claim-extract` passes with `claim_count=122285`;
  `rule-claim-link` validates with `rule_count=48`, `link_count=0`, and
  `gap_count=48`; `nepa-knowledge-graph-export` passes `72` validation checks
  with `region1_forest_plan_graph_ready_profile_count=10`; and
  `promotion-suite` now reports `full_canonical_corpus_ready=true` with `8/8`
  required full-canonical results passing.
- The prior packet
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`
  is now reduced through the active-source-set rebind. Its next routing is this dedicated
  identity-reconciliation packet, not another blind downstream rerun attempt.
- That archived replay packet is now also locally complete as a handoff
  boundary. The remaining live full-canonical route is Milestone 2 in
  `docs/FULL_CANONICAL_LIVE_SOURCE_SET_PROMOTION_MILESTONE_PLAN.md` on live
  successor `source-set-f775524ab233ff27` after Milestone 1 closeout
  `09a85f7`.

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
  on refreshed archived full-canonical source set
  `source-set-732a5a91d31736f8`.

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

- broad workbook refoundation beyond the exact direct-document recovery rows
- downloader, catalog, extraction, currentness, or graph changes unrelated to
  the exact archived full-canonical blocker surfaces in this packet
- broad multi-forest source-delta capture
- direct downstream reruns while the forest-plan identity contracts are still mixed
- review-ready East Crazies or expansion-slot work

## Owner Surfaces

- `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- `src/usfs_r1_ea_sources/download.py`
- `src/usfs_r1_ea_sources/catalog.py`
- `src/usfs_r1_ea_sources/extract.py`
- `src/usfs_r1_ea_sources/extraction_accuracy.py`
- `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`
- `src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py`
- `src/usfs_r1_ea_sources/forest_plan_components.py`
- `tests/test_download.py`
- `tests/test_catalog.py`
- `tests/test_extract.py`
- `tests/test_extraction_accuracy.py`
- `tests/test_nepa_knowledge_graph_export.py`
- `tests/test_forest_plan_identity_reconciliation.py`
- `tests/test_forest_plan_component_retrieval_eval.py`
- `tests/test_forest_plan_components.py`
- `config/r1_forest_plan_identity_reconciliation_v1.json`
- `config/r1_forest_plan_component_inventory_build_manifest.json`
- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `config/forest_plan_component_retrieval_eval_v1.json`
- `config/forest_plan_profiles.json`
- `config/r1_forest_plan_document_register_draft.csv`
- `docs/architecture_contract.toml`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`
- `source_library/derived/source-set-732a5a91d31736f8/forest_plan_components/summary.json`
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

- Weak point forecast: manifest rebind work could hide the still-unresolved rows by simply
  removing them from the active accounting surface.
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
- Closing commit hash:
  `7dd4fb5` (`Reduce identity reconciliation Milestone 1 source-record mix`)
- Closed `2026-05-19` through `7dd4fb5`: the committed manifest and readiness configs now carry only the `25`
  unresolved legacy `R1PLAN-*` rows, while the `74` exact URL-backed rows are rebound onto active
  canonical source-record IDs with governed `identity_reconciliation` blocker metadata.

### Milestone 2: Reconcile Retrieval Component Identities

Outcome label: resolved

- Govern the remaining Flathead primary-plan rebind in
  `config/r1_forest_plan_document_register_draft.csv` through
  `existing_source_record_id=FINAL-FLAT-001`, then regenerate the committed
  identity registry plus the bound manifest/readiness surfaces.
- Align `config/forest_plan_profiles.json` so the Flathead active plan and
  supporting primary-plan role both point at `FINAL-FLAT-001`.
- Rebuild the archived full-canonical forest-plan component inventory on
  `source-set-370896a1043817f2` and keep the retrieval contract blocked unless
  that build becomes truthful again.
- Rebind `config/forest_plan_component_retrieval_eval_v1.json` away from
  legacy `R1PLAN-*` component IDs and onto the canonical component IDs emitted
  by that rebuilt inventory.
- Closed `2026-05-19` in the current local milestone closeout: the governed
  Flathead rebind reduces the registry to `74` exact URL matches,
  `1` governed catalog rebound, and `24` unresolved rows; the archived
  `forest-plan-components-build` replay now passes with `1416` components and
  `397` standards; and `forest-plan-component-retrieval-eval` now passes
  `6/6` on canonical component IDs.

### Milestone 3: Reduce Archived Full-Canonical Downstream Blocker To Direct-Document Lane

Outcome label: reduced

- Repair the archived parser/runtime boundary first so downstream graph
  failures are measured against the real archived source-set contract rather
  than a mixed active-catalog fallback.
- Close the archived extraction lane truthfully on
  `source-set-370896a1043817f2`: keep the derived replay green at `634/634`
  extracted rows, ship the managed `rapidocr` and `cryptography` runtime
  dependencies, and rerun the archived audit until the remaining blocker
  family is explicit.
- Close the milestone only when the residual full-canonical stop condition is
  recorded truthfully as the `11` wrapper-page direct-document rows
  `FPS-420`, `LEX-USFS-002`, `LEX-USFS-003`, `LEX-USFS-007`,
  `LEX-USFS-008`, `LEX-USFS-011`, `LEX-USFS-012`, `LEX-USFS-013`,
  `LEX-USFS-016`, `LEX-USFS-017`, and `WILD-ESA-075`, with downstream
  retrieval, claim, rule-claim, and graph failures described as consequences
  of that admission block rather than as a standalone graph-only gap.
- Closing commit hash:
  `9a9e012` (`Reduce archived full-canonical graph blocker to direct-document lane`)
- Reduced `2026-05-19` through `9a9e012`: archived extraction now remains
  green at `634/634`, the managed `extraction` extra includes `rapidocr` and
  `cryptography`, `extraction-accuracy-audit` now admits `332/343` required
  active-review rows, `retrieval-build` fails only on the `11` direct-document
  rows above, `claim-extract` now materializes `120689` claims but fails
  validation because retrieval is not reviewer-ready, `rule-claim-link` fails
  closed on claim validation, and `promotion-suite` remains `6/8` with
  `full_canonical_failure_category_counts={"graph_viewer_export_invalid": 2}`
  understood as downstream of that `11`-row blocker family.

### Milestone 4: Recover The Direct-Document Residual And Resume Downstream Reruns

Outcome label: resolved

- Closing commit hash:
  `237c45d` (`Resolve archived full-canonical Milestone 4 lane`)

- Replace or governably rebind the `11` wrapper-page direct-document rows
  still rejected by the verified-extraction admission gate on archived
  full-canonical source set `source-set-732a5a91d31736f8`.
- Rerun `retrieval-build`, then rerun `claim-extract`,
  `rule-claim-link`, `nepa-knowledge-graph-export`, and
  `promotion-suite` on `source-set-732a5a91d31736f8`.
- Close only when the archived admission gate is green, retrieval is
  reviewer-ready, validated `claims.jsonl` and `rule_claim_links.jsonl`
  regenerate truthfully, and `promotion-suite` no longer reports
  `graph_viewer_export_invalid`.
- Resolved `2026-05-19` in the current local closeout: the workbook now points
  the `LEX-USFS-*` and `WILD-ESA-075` rows at direct official PDFs, `FPS-420`
  now admits through ZIP metadata extraction, the archived replay now emits
  `source-set-732a5a91d31736f8`, `extraction-accuracy-audit` passes with zero
  blocked rows, and the downstream archived chain is green through
  `promotion-suite` with `full_canonical_corpus_ready=true` and `8/8`
  required full-canonical results passing.

### Milestone 5: Durable Closeout And Routing Reset

Outcome label: resolved

- Closing commit hash:
  `df2bd28` (`Resolve archived full-canonical Milestone 5 closeout`)

- Update the durable routing set so this packet is marked resolved instead of
  continuing to route a phantom Milestone 5 follow-on.
- Record the docs-only closeout and verification commands in
  `docs/SESSION_HANDOFF.md`.
- Resolved `2026-05-19` in the current local closeout: the active routing set
  now describes the archived full-canonical lane as green on
  `source-set-732a5a91d31736f8`, preserves `237c45d` as the runtime closeout,
  and stops routing another archived replay through this packet.

## Required Implementation Artifacts

- `src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py`
- `tests/test_forest_plan_identity_reconciliation.py`
- `config/r1_forest_plan_identity_reconciliation_v1.json`
- `config/r1_forest_plan_component_inventory_build_manifest.json`
- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `config/forest_plan_profiles.json`
- `config/forest_plan_component_retrieval_eval_v1.json`
- `docs/architecture_contract.toml`
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
- Milestone 1 manifest/readiness contract gate:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_identity_reconciliation.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profiles.py tests/test_forest_plan_profile_eval_contracts.py -q`
- Milestone 2 inventory/retrieval gate:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_identity_reconciliation.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profiles.py tests/test_forest_plan_profile_eval_contracts.py tests/test_forest_plan_component_retrieval_eval.py tests/test_forest_plan_components.py tests/test_phase_eval_direct_eval_contracts.py tests/test_phase_eval.py tests/test_promotion_suite.py -q`
- Milestone 3 archived parser/runtime gate:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_extract.py tests/test_extraction_accuracy.py tests/test_retrieval.py tests/test_claim_extraction.py -q`
- Milestone 4 archived direct-document and downstream rerun gate:
  `PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library --source-set-id source-set-732a5a91d31736f8`
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-732a5a91d31736f8`
  `PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id source-set-732a5a91d31736f8`
  `PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link --output-dir source_library --source-set-id source-set-732a5a91d31736f8`
  `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-732a5a91d31736f8`
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
- Architecture contract gate:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py -q`
- Source/test lint:
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/download.py src/usfs_r1_ea_sources/catalog.py src/usfs_r1_ea_sources/extract.py src/usfs_r1_ea_sources/extraction_accuracy.py src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py src/usfs_r1_ea_sources/forest_plan_components.py tests/test_download.py tests/test_catalog.py tests/test_extract.py tests/test_extraction_accuracy.py tests/test_nepa_knowledge_graph_export.py tests/test_forest_plan_identity_reconciliation.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profiles.py tests/test_forest_plan_profile_eval_contracts.py tests/test_forest_plan_component_retrieval_eval.py tests/test_forest_plan_components.py tests/test_phase_eval_direct_eval_contracts.py tests/test_phase_eval.py tests/test_promotion_suite.py`
- Plan lint:
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/FULL_CANONICAL_FOREST_PLAN_IDENTITY_RECONCILIATION_MILESTONE_PLAN.md`
- Docs and closeout:
  `git diff --check`

## Acceptance Criteria

- `config/r1_forest_plan_identity_reconciliation_v1.json` exists and records the active source set
  as `source-set-9e7d85759951c279`.
- The committed registry records `99` referenced legacy source-record IDs, `74` exact URL-backed
  canonical bindings, `1` governed catalog rebound, and `24` unresolved rows.
- The committed manifest/readiness pair now reduces to exactly those `74` exact canonical
  source-record IDs plus the `1` governed rebound and the explicit unresolved
  `24`-row legacy blocker set.
- The unresolved status split is explicit and preserved at
  `catalog_confirmed=11` and `source_delta_required=13`.
- The archived full-canonical `forest-plan-components-build` replay now passes
  with `component_count=1416`, `standard_count=397`, and
  `blocked_forest_unit_ids=[]`.
- `forest-plan-component-retrieval-eval` now passes `6/6` on canonical
  component IDs for the refreshed archived source set.
- Focused tests prove the committed registry and the live manifest/readiness pair stay aligned on
  that rebound identity mix.
- The active routing set no longer treats the reduced Milestone 3 rerun packet
  as the active implementation surface, and this packet no longer leaves a
  pending Milestone 5 residual after the docs-only closeout.

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

- The broader full-canonical source-set refresh/rebind decision and the
  narrowed Flathead/retrieval repair are now complete through archived replay
  source set `source-set-732a5a91d31736f8`.
- The archived runtime lane is now green end to end. On the refreshed archived
  source set, `forest-plan-components-build` validates `10/10` forests,
  `forest-plan-component-retrieval-eval` passes `6/6`,
  `extraction-accuracy-audit` admits all `343` required active-review rows,
  `retrieval-build` is reviewer-ready, and the claims, rule-claim, graph, and
  promotion-suite layers all validate truthfully.
- The former Milestone 5 packet-closeout hygiene slice is now resolved. This
  packet no longer owns an active rerun or docs-only follow-on.
- Any future work against the explicit `24` unresolved legacy rows must open a
  fresh packet with its own bounded goal rather than reactivating this
  archived full-canonical closeout plan by default.
- If a future session cannot prove a canonical binding for one of the `24` unresolved rows, it must
  keep that row explicit as unresolved rather than hiding it inside a broad rerun attempt.
