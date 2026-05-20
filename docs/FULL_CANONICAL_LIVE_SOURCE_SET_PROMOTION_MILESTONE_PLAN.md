# Full Canonical Live Source-Set Promotion Milestone Plan

Date: 2026-05-19
Status: Milestone 0 resolved 2026-05-19 through routing rebaseline; Milestone 1 resolved 2026-05-19 through `09a85f7` with live successor `source-set-f775524ab233ff27`; Milestone 2 resolved locally 2026-05-19 through live component-inventory parity on `source-set-f775524ab233ff27`; Milestone 3 is the next routed slice
Owner context: `/Users/chunkstand/projects/usfs-r1-EA-sources` live full-canonical source-set promotion boundary

## Purpose

The repo now has a split full-canonical truth:

- the live imported catalog plus extraction/currentness boundary in
  `source_library/catalog/` is now `source-set-f775524ab233ff27`, and
- the governing green full-canonical downstream contract is the refreshed archived replay
  `source-set-732a5a91d31736f8`.

This milestone exists to remove that split truth the right way. It does not paper over the gap by
renaming `source-set-9e7d85759951c279` in docs or configs. Instead, it emits a new live successor
source set from the existing canonical download run under current `HEAD`, replays the full-canonical
forest-plan and downstream lanes on that live successor, then promotes that successor as the sole
governing full-canonical source set.

The intent of that promoted live source set must remain explicit: it is the system's broader
validated authority corpus, not a narrow forest-plan-only lane. The promoted live successor must be
the default full knowledge base covering laws, regulations, policies, directives, handbooks, forest
plans, and supporting documents that the system must consider before any review-specific narrowing.

## Current Evidence

- `source_library/catalog/source_set_manifest.json` now records live successor
  `source-set-f775524ab233ff27` with `source_count=634`, `artifact_count=622`,
  `source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`,
  `document_role_counts.forest_plan=34`, `document_role_counts.forest_plan_support=315`, and
  `document_role_counts.regulation=44`.
- `reuse-inventory --source-set-id source-set-f775524ab233ff27 --previous-source-set-id source-set-732a5a91d31736f8`
  now classifies `reuse_extraction=634` and `needs_extract=0`, and
  `source_library/derived/source-set-f775524ab233ff27/diagnostics/summary.json`
  is green with `extracted_count=634`, `failed_count=0`, `chunk_count=98699`,
  `reused_count=634`, and `validation_passed=true`.
- `source_library/derived/source-set-f775524ab233ff27/authority_currentness/authority_currentness_report.json`
  is present and green.
- `source_library/derived/source-set-f775524ab233ff27/forest_plan_components/summary.json`
  is now present and green with `component_count=1416`,
  `standard_count=397`, `coverage_passed=true`,
  `component_source_accuracy_passed=true`, and
  `blocked_forest_unit_ids=[]`, but
  `retrieval/summary.json`, `claims/summary.json`,
  `knowledge_graph/nepa_3d_graph_validation.json`, and
  `knowledge_graph/nepa_3d_graph_summary.json` are not yet present for that
  live source set.
- The previous live negative proof `source-set-9e7d85759951c279` remains
  historical context only after Milestone 2. The active live blocker is no
  longer stale catalog shape or the forest-plan component inventory; it is the
  still-unreplayed downstream full-canonical chain on
  `source-set-f775524ab233ff27`.
- The refreshed archived gate at
  `source_library/runs/phase2-canonical-full-canonical-classifier-refresh-20260519/catalog_gate/`
  emits `source-set-732a5a91d31736f8` from the same governing download run
  `phase2-canonical-download-full-post-fps005-removal-20260519`, but with
  `document_role_counts.forest_plan=34`, `document_role_counts.forest_plan_support=315`, and
  `document_role_counts.regulation=44`.
- `source_library/derived/source-set-732a5a91d31736f8/forest_plan_components/summary.json` is
  green with `component_count=1416`, `standard_count=397`, `coverage_passed=true`, and
  `component_source_accuracy_passed=true`.
- `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md` consistently describe the active
  canonical register and full knowledge base as the broader authority corpus: laws, regulations,
  policies, directives, handbooks, forest plans, and supporting documents visible before
  review-specific narrowing. This promotion packet must preserve that intent rather than describing
  the live successor as only a forest-plan repair lane.
- The live component-inventory contract configs now point at the live
  successor:
  `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  and `config/r1_forest_plan_identity_reconciliation_v1.json`.
- The downstream full-canonical contract configs still point at the archived
  source set, not yet the live successor:
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `config/forest_plan_component_retrieval_eval_v1.json`,
  `config/phase_eval_direct_eval_v1.json`, and
  `config/promotion_suite_v1.json`.
- `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  still reports `full_canonical_corpus_ready=true`, but it does so for
  `full_canonical_source_set_id=source-set-732a5a91d31736f8`, not for live
  successor `source-set-f775524ab233ff27`.
- The durable routing set is now aligned through Milestone 2 closeout:
  `README.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`, and the two superseded full-canonical
  forest-plan packets all describe `source-set-f775524ab233ff27` as the
  resolved live catalog plus extraction/currentness/component-inventory
  boundary and Milestone 3 as the next routed slice.
- The former stale-prose risk is now explicitly bounded to preserved historical
  context: the superseded full-canonical forest-plan packets label their
  `source-set-9e7d85759951c279` references as historical and route active live
  promotion through this packet instead.

## Goal

Promote a single live full-canonical source set by:

- re-emitting the live catalog from
  `phase2-canonical-download-full-post-fps005-removal-20260519` under current `HEAD`,
- capturing the emitted live successor source-set ID,
- preserving the source-register intent that the emitted successor remains the broader authority
  corpus sourced from `Document_Register_Master`, not a narrowed forest-plan subset,
- replaying the full-canonical forest-plan and downstream lanes on that live successor,
- repointing every full-canonical contract surface from archived `source-set-732a5a91d31736f8`
  to the live successor, and
- closing with `promotion-suite` green on the live successor so archived `732a...` becomes
  preserved evidence only, not the governing live dependency.

## Non-Goals

- Do not declare `source-set-9e7d85759951c279` promoted by changing prose or config only.
- Do not delete or overwrite the archived `source-set-732a5a91d31736f8` evidence family before the
  live successor is green.
- Do not broaden scope into reviewer-ready East Crazies package work on
  `source-set-ba8d0feae79501b8`.
- Do not rewrite the promotion story as if the live successor exists only to serve forest-plan
  components while laws, regulations, policies, directives, handbooks, and other supporting
  authority become secondary or optional.
- Do not guess replacements for unresolved legacy `R1PLAN-*` identities by title similarity or
  forest-name similarity.
- Do not hand-edit `source_library/` JSON/JSONL outputs to manufacture a green closeout.
- Do not weaken `stale_artifact`, graph, direct-eval, or component-inventory gates just to force a
  passing promotion replay.

## Scope

- live catalog refresh from the existing canonical download run
- live extraction reuse-first refresh on the emitted successor source set
- live authority-currentness refresh on that successor source set
- live forest-plan component inventory, profile eval, component retrieval eval, retrieval, claims,
  rule-claim, graph export, and promotion reruns on that successor source set
- config rebinding for the full-canonical live contract surfaces
- durable framing and contract alignment that preserves the broader laws/regulations/policies/
  directives/handbooks/forest-plan/supporting-document intent of the promoted live source set
- durable docs and handoff updates that retire the split live-vs-archived truth

## Out Of Scope

- a new workbook contract or new bulk download run unless the existing canonical run proves
  insufficient
- broad recapture of `Document_Register_Master`
- new source-delta capture for the `24` unresolved registry rows unless a rerun proves the live
  promotion path cannot close without it
- current-promotion review-lane changes for `source-set-ba8d0feae79501b8`
- removal of historical archived artifacts from `source_library/runs/`

## Owner Surfaces

- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`
- `source_library/catalog/catalog_validation.json`
- `source_library/derived/<live-successor-source-set-id>/diagnostics/`
- `source_library/derived/<live-successor-source-set-id>/authority_currentness/`
- `source_library/derived/<live-successor-source-set-id>/forest_plan_components/`
- `source_library/derived/<live-successor-source-set-id>/retrieval/`
- `source_library/derived/<live-successor-source-set-id>/claims/`
- `source_library/derived/<live-successor-source-set-id>/knowledge_graph/`
- `source_library/evaluations/forest_plan_profile/`
- `source_library/evaluations/forest_plan_component_retrieval/`
- `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/`
- `config/r1_forest_plan_component_inventory_build_manifest.json`
- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `config/region1_forest_plan_profile_eval_coverage_v1.json`
- `config/forest_plan_component_retrieval_eval_v1.json`
- `config/phase_eval_direct_eval_v1.json`
- `config/promotion_suite_v1.json`
- `config/r1_forest_plan_identity_reconciliation_v1.json`
- `config/forest_plan_profiles.json` only if the rerun proves an active live contract still depends
  on legacy IDs beyond the governed unresolved registry set
- `src/usfs_r1_ea_sources/catalog.py` and other existing runtime owners only if the live rerun still
  diverges from the archived classifier-refresh path under current `HEAD`
- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`
- `docs/FULL_CANONICAL_FOREST_PLAN_IDENTITY_RECONCILIATION_MILESTONE_PLAN.md`
- this plan file

## Placement Rules

- Emit the promoted live source set through the normal `catalog-build` and `extract-build` command
  paths. Do not rename `source-set-9e7d85759951c279` or copy archived `732a...` artifacts into live
  paths by hand.
- Keep the archived `source-set-732a5a91d31736f8` family preserved as historical evidence until the
  live successor is green and the durable docs are aligned.
- Do not repoint full-canonical config surfaces to the live successor until the successor exists and
  the prerequisite forest-plan component inventory passes on that successor.
- Keep identity reconciliation governed through
  `config/r1_forest_plan_identity_reconciliation_v1.json`. Do not introduce a second ad hoc
  override surface for this packet.
- If the live rerun still diverges from the archived replay under the same download run, fix the
  existing catalog/forest-plan/runtime owner surfaces. Do not introduce a parallel one-off replay
  script as the only durable recovery path.
- Any change to `config/forest_plan_profiles.json` must be exact-URL-backed by the registry or
  justified by the emitted live component inventory. Do not mass-rewrite profile source-record IDs
  just to make the reruns pass.
- Repo policy still treats `source_library/` as local evidence. Unless the user explicitly changes
  repo policy, reference those generated artifacts in docs and handoff rather than staging them.

## Weak-Point Prevention Contract

### Weak Point 1: paper promotion replaces real live replay

- Weak point forecast: a future session may flip `full_canonical_source_set_id` in configs and docs
  before a new live successor exists, creating a fake promotion.
- Owner surface: `config/promotion_suite_v1.json`, the full-canonical config suite, and durable
  routing docs.
- Prevention gate: the live successor source-set ID must be present in
  `source_library/catalog/source_set_manifest.json`, must differ from `source-set-9e7d85759951c279`,
  and must own green `forest_plan_components`, graph, and promotion artifacts before the config flip
  closes.
- Fail threshold: configs or docs claim live promotion while the live catalog still points at
  `source-set-9e7d85759951c279` or while the live successor lacks the required downstream artifacts.
- Controlled violation: the current repo state already supplies the negative proof. Live `9e7d...`
  fails the component inventory while the archived lane is green; the milestone must preserve that
  distinction until a new live successor proves otherwise.
- Future-Codex misuse scenario: editing `config/promotion_suite_v1.json` first because it makes the
  report header look green. This packet forbids that shortcut.

### Weak Point 2: stale live catalog shape survives under a new source-set label

- Weak point forecast: the live rerun could emit a new source-set ID but still carry the stale
  `9`-plan / `26`-support role split, leaving the live lane functionally equivalent to `9e7d...`.
- Owner surface: live catalog manifest, live catalog JSONL, and `catalog.py`.
- Prevention gate: the emitted live successor manifest must match the corrected current-HEAD role
  split from the archived classifier-refresh gate, unless the same milestone ships a stronger,
  documented replacement contract.
- Fail threshold: the emitted live successor still reports the stale live role shape or still leaves
  the five blocked forests unresolved at the component-inventory boundary.
- Controlled violation: the current live-vs-archived manifest mismatch is the negative case. This
  milestone closes only when that mismatch is gone on the live lane.
- Future-Codex misuse scenario: assuming any new source-set ID is automatically fresher and safer
  than `732a...`. The gate requires catalog-shape parity, not just a different ID.

### Weak Point 3: mixed archived and live source-set IDs remain in contract surfaces

- Weak point forecast: the live successor could go green while some config surfaces still require
  `732a...`, producing split truth and future replay drift.
- Owner surface: `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `config/forest_plan_component_retrieval_eval_v1.json`,
  `config/phase_eval_direct_eval_v1.json`, and `config/promotion_suite_v1.json`.
- Prevention gate: a targeted `rg` over those files after closeout must show the live successor as
  the only active full-canonical source-set ID. `source-set-732a5a91d31736f8` may remain only in
  historical docs, not in live full-canonical configs.
- Fail threshold: any active config still points full-canonical runtime checks at archived `732a...`
  after the live successor is promoted.
- Controlled violation: the current config state is the negative case. This packet closes only when
  those active configs stop requiring `732a...`.
- Future-Codex misuse scenario: fixing promotion-suite but forgetting direct-eval or readiness
  manifests. The `rg` gate forces all contract surfaces to move together.

### Weak Point 4: unresolved legacy identity debt is silently hidden instead of governed

- Weak point forecast: a future session could remove `R1PLAN-*` references wholesale without
  distinguishing exact canonical rebinds from the still-unresolved `24`-row registry set.
- Owner surface: identity registry, inventory manifest, readiness config, and any touched profile
  config.
- Prevention gate: any changed legacy source-record reference must either disappear because the live
  successor emits the canonical replacement artifact or remain listed in
  `config/r1_forest_plan_identity_reconciliation_v1.json` as an exact unresolved row.
- Fail threshold: a legacy ID disappears from a contract-bearing config without exact-URL-backed
  proof, or a new guessed canonical mapping appears with no governed registry evidence.
- Controlled violation: the existing `24` unresolved rows are the negative roster. The packet must
  either preserve them explicitly or close them with exact governed evidence.
- Future-Codex misuse scenario: mass-replacing `R1PLAN-*` strings in JSON files because the grep
  output is large. This packet requires exact governed proof for every removal.

### Weak Point 5: durable docs keep split or contradictory routing after runtime closeout

- Weak point forecast: the live successor could be promoted while `README.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and older milestone packets still tell
  future sessions to use archived `732a...` or historical `9e7d...` prose.
- Owner surface: the durable doc set and this plan file.
- Prevention gate: closeout requires a targeted doc sweep proving the governing full-canonical live
  source-set ID, the archived historical boundary, and the reviewer-ready East Crazies boundary are
  all described consistently.
- Fail threshold: any durable routing doc still describes archived `732a...` as the active
  full-canonical runtime dependency after the live successor is green, or still implies
  `source-set-9e7d85759951c279` was the already-promoted green live lane.
- Controlled violation: the preserved superseded prose in
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md` is the negative case.
- Future-Codex misuse scenario: trusting a stale plan paragraph over the current config and
  promotion artifact. The doc sweep must make that impossible.

### Weak Point 6: promotion closes mechanically but loses the broader authority-corpus intent

- Weak point forecast: a future session may describe the promoted live successor as only a
  forest-plan repair lane and silently de-emphasize the broader laws, regulations, policies,
  directives, handbooks, and supporting documents that the system must consider.
- Owner surface: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`,
  `config/promotion_suite_v1.json`, and this plan file.
- Prevention gate: closeout docs and routing notes must explicitly describe the promoted live
  successor as the default full knowledge base sourced from `Document_Register_Master`, with laws,
  regulations, policies, directives, handbooks, forest plans, and supporting documents visible
  before review-specific narrowing.
- Fail threshold: the closeout leaves the live successor framed as a forest-plan-only lane, or the
  promoted live source set no longer preserves the full canonical partition counts
  `active_review_corpus=582` and `currentness_supersession_archive=52`.
- Controlled violation: the current split-truth draft state is the negative case because it is easy
  to read the packet as a forest-plan-only replay story unless the broader authority-corpus intent
  is written directly into the governing docs.
- Future-Codex misuse scenario: replaying only the forest-plan metrics and then trimming future
  docs or configs so non-forest-plan authority looks optional. This packet requires durable wording
  and measurable partition preservation to block that drift.

## Milestone Sequence

### Milestone 0: Rebaseline The Live Promotion Packet Against Current Repo Truth

Outcome label: resolved locally

- Reconfirm the current split truth from:
  `source_library/catalog/source_set_manifest.json`,
  `source_library/runs/phase2-canonical-full-canonical-classifier-refresh-20260519/catalog_gate/source_set_manifest.json`,
  `source_library/derived/source-set-9e7d85759951c279/forest_plan_components/summary.json`,
  `source_library/derived/source-set-732a5a91d31736f8/forest_plan_components/summary.json`,
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`,
  and the active config suite listed above.
- Record the exact comparison in this plan and `docs/SESSION_HANDOFF.md` so future sessions do not
  restart from the superseded “promote `9e7d...` directly” story.
- Record in this plan and `docs/SESSION_HANDOFF.md` that the promotion target is the broader
  authority corpus sourced from `Document_Register_Master`, not only a forest-plan-specific fix.
- Close the milestone only when the packet explicitly says the target is a new live successor source
  set, not a prose rename of `source-set-9e7d85759951c279`.

### Milestone 1: Emit And Validate The Live Successor Source Set

Outcome label: resolved

- Re-run `catalog-build` from
  `phase2-canonical-download-full-post-fps005-removal-20260519` under current `HEAD` so
  `source_library/catalog/` emits a new live successor source-set ID.
- Re-run `reuse-inventory` against the archived green source set, then
  `extract-build --reuse-existing --reuse-inventory-path ...` and
  `authority-currentness` on that emitted successor.
- Compare the live successor manifest against the archived classifier-refresh manifest and require
  parity on the governing role/count contract:
  `document_role_counts.forest_plan=34`,
  `document_role_counts.forest_plan_support=315`,
  `document_role_counts.regulation=44`,
  `source_count=634`, and
  `artifact_count=622`.
- Require the emitted live successor to preserve the canonical partition breadth from the governing
  run:
  `source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`.
- Close the milestone only when:
  the live successor ID is present in `source_library/catalog/source_set_manifest.json`,
  the successor differs from `source-set-9e7d85759951c279`,
  extraction and currentness are green on the successor, and
  the stale `9`-plan / `26`-support catalog shape is gone, and
  the live lane still represents the broader canonical authority corpus rather than a narrowed
  subset.

### Milestone 2: Prove The Live Successor At The Forest-Plan Inventory Boundary

Outcome label: resolved

- Point the manifest/readiness full-canonical build surfaces at the emitted live successor.
- Re-run `forest-plan-components-build` on the live successor using
  `config/r1_forest_plan_component_inventory_build_manifest.json`.
- If that rerun still exposes legacy identity or role-classification drift, fix the existing owner
  surfaces (`catalog.py`, governed identity surfaces, or other current runtime owners) and rerun.
- Do not update downstream profile/retrieval/promotion contracts yet if the live successor cannot
  truthfully close the component inventory boundary.
- Close the milestone only when the live successor component inventory reports
  `coverage_passed=true`, `component_source_accuracy_passed=true`,
  `blocked_forest_unit_ids=[]`, `component_count=1416`, and `standard_count=397`.
- Closed locally on 2026-05-19:
  `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`, and
  `config/r1_forest_plan_identity_reconciliation_v1.json` now bind the live
  component-inventory boundary to `source-set-f775524ab233ff27`.
- `forest-plan-components-build --output-dir source_library --source-set-id source-set-f775524ab233ff27 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  passed with `component_count=1416`, `standard_count=397`,
  `blocked_forest_unit_ids=[]`, `coverage_passed=true`, and
  `component_source_accuracy_passed=true`.

### Milestone 3: Rebind And Replay The Full-Canonical Downstream Chain On The Live Successor

Outcome label: resolved

- Repoint the live full-canonical contract surfaces to the live successor:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `config/forest_plan_component_retrieval_eval_v1.json`,
  `config/phase_eval_direct_eval_v1.json`, and `config/promotion_suite_v1.json`.
- Remove active config dependence on archived gate files under
  `runs/phase2-canonical-full-canonical-classifier-refresh-20260519/catalog_gate/`.
- Re-run, in dependency order, on the live successor:
  `forest-plan-profile-eval`,
  `forest-plan-component-retrieval-eval`,
  `retrieval-build`,
  `claim-extract`,
  `rule-claim-link`,
  `nepa-knowledge-graph-export`, and
  `promotion-suite`.
- Close the milestone only when the eval and promotion artifacts themselves report the live
  successor source-set ID and the full-canonical chain is green without archived fallbacks.

### Milestone 4: Promote The Live Successor As Sole Full-Canonical Truth And Retire Archived Dependency

Outcome label: resolved

- Update `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, this plan file,
  and the two superseded forest-plan milestone packets so they describe the live successor as the
  governing full-canonical source set and `source-set-732a5a91d31736f8` as preserved historical
  evidence only.
- Make the closeout docs explicit that the promoted live successor is the default full knowledge
  base for the system, with laws, regulations, policies, directives, handbooks, forest plans, and
  supporting documents visible before any review-specific narrowing.
- Prove that active full-canonical configs no longer require `732a...`.
- Record the live successor ID, verification commands, and milestone commit hashes in the handoff.
- Close the milestone only when `promotion-suite` reports
  `full_canonical_source_set_id=<live-successor-source-set-id>`,
  `full_canonical_corpus_ready=true`, and `8/8` required full-canonical results passing.

## Required Implementation Artifacts

- a new live successor `source_library/catalog/source_set_manifest.json`
- refreshed live `source_library/catalog/source_catalog.jsonl`
- refreshed live `source_library/catalog/catalog_validation.json`
- refreshed live `source_library/derived/<live-successor-source-set-id>/diagnostics/summary.json`
- refreshed live `source_library/derived/<live-successor-source-set-id>/authority_currentness/authority_currentness_report.json`
- refreshed live `source_library/derived/<live-successor-source-set-id>/forest_plan_components/summary.json`
- refreshed live `source_library/evaluations/forest_plan_profile/forest_plan_profile_eval_results.json`
- refreshed live `source_library/evaluations/forest_plan_component_retrieval/forest_plan_component_retrieval_eval_results.json`
- refreshed live `source_library/derived/<live-successor-source-set-id>/retrieval/summary.json`
- refreshed live `source_library/derived/<live-successor-source-set-id>/claims/summary.json`
- refreshed live `source_library/derived/<live-successor-source-set-id>/knowledge_graph/nepa_3d_graph_validation.json`
- refreshed live `source_library/derived/<live-successor-source-set-id>/knowledge_graph/nepa_3d_graph_summary.json`
- refreshed live `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
- any narrow runtime/code changes required to make the live rerun match the archived classifier-refresh contract

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`
- `docs/FULL_CANONICAL_FOREST_PLAN_IDENTITY_RECONCILIATION_MILESTONE_PLAN.md`
- this plan file
- `docs/OUTPUT_SCHEMAS.md` if any output-schema or parser/runtime fields change while making the
  live successor replayable

## Required Verification Gates

- Baseline and contract truth:
  `PYTHONPATH=src python -m usfs_r1_ea_sources validate-run --output-dir source_library --run-id phase2-canonical-download-full-post-fps005-removal-20260519`
- Live catalog refresh:
  `PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --run-id phase2-canonical-download-full-post-fps005-removal-20260519`
- Live extraction and currentness refresh:
  `PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory --output-dir source_library --source-set-id <live-successor-source-set-id> --previous-source-set-id source-set-732a5a91d31736f8`
  `PYTHONPATH=src python -m usfs_r1_ea_sources extract-build --output-dir source_library --reuse-existing --reuse-inventory-path source_library/derived/<live-successor-source-set-id>/reuse_inventory/reuse_inventory.json`
  `PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness --output-dir source_library --source-set-id <live-successor-source-set-id>`
- Forest-plan promotion boundary:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id <live-successor-source-set-id> --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json`
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-retrieval-eval --output-dir source_library --manifest config/forest_plan_component_retrieval_eval_v1.json`
- Downstream replay:
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id <live-successor-source-set-id>`
  `PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id <live-successor-source-set-id>`
  `PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link --output-dir source_library --source-set-id <live-successor-source-set-id>`
  `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id <live-successor-source-set-id>`
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
- Focused contract/test coverage:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profile_eval_contracts.py tests/test_phase_eval_direct_eval_contracts.py tests/test_phase_eval.py tests/test_catalog.py tests/test_forest_plan_source_delta_readiness.py -q`
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/catalog.py tests/test_catalog.py tests/test_forest_plan_source_delta_readiness.py tests/test_promotion_suite.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profile_eval_contracts.py tests/test_phase_eval_direct_eval_contracts.py tests/test_phase_eval.py`
  `PYTHONPATH=src python -m compileall src`
- Config/doc drift checks:
  `rg -n "source-set-732a5a91d31736f8" config/promotion_suite_v1.json config/region1_forest_plan_profile_eval_coverage_v1.json config/forest_plan_component_retrieval_eval_v1.json config/phase_eval_direct_eval_v1.json config/r1_forest_plan_component_inventory_build_manifest.json config/region1_forest_plan_readiness_nepa_3d_v1.json`
  `git diff --check`
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/FULL_CANONICAL_LIVE_SOURCE_SET_PROMOTION_MILESTONE_PLAN.md`

## Acceptance Criteria

- `source_library/catalog/source_set_manifest.json` emits a live successor source-set ID that is not
  `source-set-9e7d85759951c279`.
- The emitted live successor is produced from
  `phase2-canonical-download-full-post-fps005-removal-20260519`.
- The emitted live successor remains rooted in `Document_Register_Master` as the sole live load
  table and preserves
  `source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`.
- The live successor manifest matches the corrected current-HEAD catalog role split now proven in the
  archived classifier-refresh gate:
  `document_role_counts.forest_plan=34`,
  `document_role_counts.forest_plan_support=315`,
  `document_role_counts.regulation=44`,
  `source_count=634`, and
  `artifact_count=622`.
- Live extraction and authority-currentness are green on the live successor.
- `forest-plan-components-build` is green on the live successor with no blocked forests and no loss
  of source-accuracy validation.
- `forest-plan-profile-eval` results point at the live successor and pass with `covered_profile_count>=10`
  and `profile_failure_count=0`.
- `forest-plan-component-retrieval-eval` results point at the live successor and pass with
  `case_count>=6` and no failed cases.
- `source_library/derived/<live-successor-source-set-id>/retrieval/summary.json`,
  `claims/summary.json`, `knowledge_graph/nepa_3d_graph_validation.json`, and
  `knowledge_graph/nepa_3d_graph_summary.json` all exist and validate the live successor.
- `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  reports `full_canonical_source_set_id=<live-successor-source-set-id>`,
  `full_canonical_corpus_ready=true`,
  `passed_required_full_canonical_result_count=8`, and
  `full_canonical_failure_category_counts={}`.
- After closeout, the active full-canonical config surfaces no longer require
  `source-set-732a5a91d31736f8`.
- Durable docs describe one governing live full-canonical source set, one reviewer-ready East
  Crazies lane, and archived `732a...` as preserved historical evidence only.
- Durable docs describe the promoted live successor as the default full validated knowledge base
  covering laws, regulations, policies, directives, handbooks, forest plans, and supporting
  documents before any review-specific narrowing.

## Stop Conditions

- Re-running `catalog-build` from
  `phase2-canonical-download-full-post-fps005-removal-20260519` under current `HEAD` still emits a
  live catalog with the stale `9`-plan / `26`-support shape, proving a deeper runtime-path mismatch
  that needs its own investigation packet.
- The live successor can reach extraction/currentness green but cannot close the forest-plan
  component inventory boundary without guessed canonical mappings for unresolved `R1PLAN-*` rows.
- The live promotion path unexpectedly requires a new workbook contract, a broad fresh download
  campaign, or staged `source_library/` policy changes that the user has not approved.
- Any required gate can be satisfied only by weakening stale-artifact checks, direct-eval contracts,
  or forest-plan component gates.

## Local Commit Closeout Policy

- Close one milestone at a time with one local atomic commit after its verification passes.
- Stage only the verified milestone slice.
- Leave unrelated dirty or untracked files untouched.
- Include code, config, tests, plan updates, current-state docs, and handoff updates for that
  milestone in the same commit.
- Because `source_library/` is gitignored, treat those generated outputs as local evidence artifacts:
  reference their paths, source-set IDs, and key counts in the handoff and doc set instead of
  staging them unless the user explicitly changes repo policy.
- Record each milestone commit hash in `docs/SESSION_HANDOFF.md`.
- Treat a verified but uncommitted milestone as ready-to-close, not complete.

## Residual Risks And Next Milestone Routing

- If the live successor replay closes green, archived `source-set-732a5a91d31736f8` should remain as
  preserved historical evidence only. Future work should route from the promoted live successor, not
  from the archived gate.
- If the live catalog refresh still diverges from the archived classifier-refresh lane under current
  `HEAD`, stop and open a dedicated live-vs-archived catalog divergence packet rather than rewriting
  promotion docs again.
- If the unresolved `24`-row registry set becomes the real blocker to live promotion after the
  forest-plan component inventory rerun, route the remaining work into a separate source-delta or
  identity-closeout packet instead of hiding that debt inside this promotion packet.
