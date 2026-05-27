# Lolo Tyler's Kitchen Current Workbook Source-Set Rebaseline Blocker Milestone Plan

Date: 2026-05-27

Status: Resolved locally through Milestones 2-3 after the source-record identity
child replayed Lolo onto the current-workbook owner. Milestone 0 proved
`source-set-f70ea11e04ae3d53` is not a drop-in current-workbook owner for the
historical `source-set-5e65d845ce77e1a0` review artifacts. Milestone 1 then
reached an exact local-replay stop: tracked replay config rejects an ad hoc
`f70...` override, and the remaining blocker is the split source-record identity
contract now routed to
`docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`.
That child packet has since implemented the generic identity gate, resolved the
five ambiguous multi-target mappings with explicit governed identity selectors,
made the current-workbook candidate identity gate green, moved the tracked
Lolo replay/eval config surfaces to `source-set-f70ea11e04ae3d53`, and proved
`v1-ea-eval` plus review `phase-eval` green. Current-workbook owner selection
is no longer the live blocker; the remaining Lolo work returns to the broader
example-package parent for registry promotion and aggregate threshold ratchet.

Owner context: standalone child packet opened from
`docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`.
The tracked Lolo review `region1-example-lolo-tylers-kitchen-66344` now has
green review-local applicability, generated rule pack, applicability validation,
forest-plan component eval, compliance review, `v1-ea-eval`, and `phase-eval`
artifacts on `source-set-f70ea11e04ae3d53`. The older `5e65...` source set
remains historical evidence only and is not treated as current-workbook ready.

## Latest Local Implementation

- Source-register currentness Milestones 0-2 resolved by stop. They did not edit
  ignored `source_library/` manifests and did not weaken
  `source_register_contract`.
- Milestone 0 of this packet is reduced locally. The chosen owner path is not a
  manifest swap. Lolo must either replay review-local artifacts against a
  governed current-workbook owner or stop at the first artifact family whose
  source-record identity cannot be reconciled locally.
- Milestone 1 of this packet is reduced locally by exact stop. A direct
  current-workbook replay override is blocked by the tracked replay context, and
  the expected source-record IDs are split across compliance reconciliation and
  forest-plan identity reconciliation owner surfaces.
- The child source-record identity packet is now resolved through Milestones 2-3:
  `source-record-identity-gate` proves all 60 Lolo expected IDs have present
  `f70...` catalog coverage at the predecessor checkpoint and now returns
  `passed=true` for the final 59-ID eval contract after
  `identity_source_record_id` selectors resolved the five former ambiguous
  current-catalog mappings. The tracked Lolo replay context, v1 eval contract,
  applicability adjudication, forest-plan component eval contract, and
  component adjudication now all consume `source-set-f70ea11e04ae3d53`.
- The final replay closeout on `source-set-f70ea11e04ae3d53` is green:
  source-record identity gate `59/59`, `v1-ea-eval`
  `contract_status="reviewer_ready"`, `broader_ea_passed=true`,
  `forest_plan_passed=true`, and review `phase-eval` `28/28` with
  `blockers=[]` and `identity_mismatch_phase_count=0`.
- Exact readback found:
  - tracked replay context now:
    `source_set_id="source-set-f70ea11e04ae3d53"` and
    `catalog_dir="source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"`;
  - active global catalog manifest:
    `source-set-4fb59e9eb43045cb`, workbook SHA
    `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`;
  - archived current-workbook catalog gate:
    `source-set-f70ea11e04ae3d53`, workbook SHA
    `1b62348930fa9c3595bea24b6ab4cfa4c7b0a3d2c29c1f1cfefebcf9d270cf97`;
  - no exact archived `source-set-5e65d845ce77e1a0` manifest;
  - `5e65...` selected source-record IDs count `350`, while the `f70...`
    catalog source-record IDs count `708`;
  - sampled mismatch shape is `R1EA-*` IDs missing from `f70...` and `FED-*`
    IDs extra in `f70...`, so source-record identity must be handled by a
    governed replay/crosswalk decision rather than a manifest-only path swap.
- Milestone 1 identity evidence found:
  - the Lolo v1 eval contract expects 60 source-record IDs;
  - 8 expected IDs are present directly in the `f70...` catalog surface;
  - `config/compliance_source_record_reconciliation_v1.json` maps 51 absent
    expected IDs to current-workbook catalog IDs;
  - `R1PLAN-lolo-nf-02` is not in the compliance reconciliation registry but is
    separately reconciled by
    `config/r1_forest_plan_identity_reconciliation_v1.json` to `FPS-298`;
  - five compliance-reconciled expected IDs mapped to multiple current catalog
    records at this checkpoint. The child identity gate follow-on has since
    resolved them through explicit `identity_source_record_id` selectors in
    `dd3c322`, so coverage evidence and replay identity are now separated;
  - historical-to-current extraction-manifest hash matching is supporting
    evidence only, not an owner contract, because it includes unmatched
    historical rows and one-to-many fanout.
- Fresh review `phase-eval` remains fail-closed at `18/23`; the live red phases
  at that predecessor checkpoint were `retrieval`, `rule_claim_binding`,
  `downstream_direct_evaluation`, `source_register_contract`, and
  `evaluation_coverage`. Those are no longer live on the current-workbook
  replay owner after the source-record identity child closeout; current review
  `phase-eval` passes `28/28` on `source-set-f70ea11e04ae3d53`.

## Purpose

Choose or rebuild the current-workbook source-set owner for the Lolo Tyler's
Kitchen review without pretending the historical `5e65...` derived artifacts are
current against the active workbook.

This packet exists because the smaller source-register currentness packet proved
that no exact current `5e65...` manifest exists locally. The next truthful work is
therefore an owner rebaseline: either select a governed current-workbook source
set and regenerate the Lolo review artifacts against it, or create the smallest
new current-workbook catalog/currentness surface needed for that review.

## Current Evidence

- `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json` now
  points to `source-set-f70ea11e04ae3d53` and
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`.
- `source_library/catalog/source_set_manifest.json` still points to
  `source-set-4fb59e9eb43045cb` with older workbook SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`.
- `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_set_manifest.json`
  points to current-workbook `source-set-f70ea11e04ae3d53` with workbook SHA
  `1b62348930fa9c3595bea24b6ab4cfa4c7b0a3d2c29c1f1cfefebcf9d270cf97`.
- `source-set-f70ea11e04ae3d53` cannot be used as a silent drop-in manifest for
  `5e65...`: its catalog source-record set does not match the `5e65...`
  extraction manifest selected source-record set.
- Milestone 0 owner decision: `f70...` is a current-workbook catalog candidate,
  not the selected Lolo owner by itself.
- Milestone 1 stop decision: the first unreplayable surface is source-record
  identity. The replay CLI correctly rejects a `source-set-f70ea11e04ae3d53`
  override while tracked replay context still declares
  `source-set-5e65d845ce77e1a0`, and tracked eval/config cannot safely move to
  `f70...` until one replay-facing identity contract can resolve the split
  `R1EA-*`, `R1PLAN-*`, `FPS-*`, and current-workbook IDs. That stop is now
  historical: the child identity packet resolved it and moved tracked config to
  `f70...`.
- Current closeout decision: `source_register_contract`, direct-eval identity,
  and evaluation coverage now pass for the Lolo review on the current-workbook
  owner. This packet does not itself change forest-specific example registry or
  promotion roster semantics.
- The `5e65...` authority-currentness report is historically green but not a
  current source-register owner: it was generated on `2026-05-11T00:40:55Z`
  from a `source_library/catalog/source_set_manifest.json` hash
  `77361eec5963677104bf06dabe3f3d2934bfb75eae18990532d6054ba58152eb`, and no
  local `source_set_manifest.json` currently matches that hash.

## Goal

Leave the repository with one exact current-workbook Lolo owner outcome:

- either a governed current-workbook source set is chosen and the tracked Lolo
  replay/eval contracts plus review-local artifacts are regenerated against it;
  or
- a new narrower blocker is opened only after proving which required catalog,
  extraction, applicability, review, or direct-eval surface cannot be rebuilt in
  this packet.

Completion means all of the following are true:

- no active docs treat historical `5e65...` as current-workbook ready;
- no active docs use `f70...` as a drop-in Lolo manifest without a full governed
  review-artifact replay;
- `phase-eval` and `v1-ea-eval` readback govern any readiness claim;
- current promotion, strict expansion, and governed roster semantics are not
  weakened.

## Non-Goals

- Do not hand-edit ignored `source_library/` manifests or result JSON.
- Do not make `source_register_contract` optional or ignore workbook SHA drift.
- Do not admit Lolo into `config/v1_real_package_review_coverage_v1.json` or
  `config/promotion_suite_v1.json` from this packet; registry and promotion
  changes belong to the broader example-package Milestone 3 aggregate-gate
  slice.
- Do not rerun network download workflows unless a milestone first proves local
  catalog/currentness replay cannot satisfy the gate.
- Do not repair retrieval quality or direct-eval thresholds in this packet until
  the current-workbook source-set owner is coherent.

## Scope

- Lolo Tyler's Kitchen replay context and eval contract owner source set
- current-workbook catalog/currentness manifest selection or rebuild
- local generated artifact regeneration needed to move review-local Lolo
  artifacts from historical `5e65...` to the chosen current-workbook owner
- phase-eval and v1-ea-eval readback
- current routing, current-state, handoff, and lineage docs

## Out Of Scope

- ECID historical slot semantics
- South Plateau, West Reservoir, or ECID reviewer-ready replay changes
- governed promotion roster changes
- broad downloader recapture unless selected by a later stop condition
- retrieval semantic-quality repair after currentness is fixed

## Owner Surfaces

- live blocker docs:
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/AGENT_START_HERE.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`
- parent and lineage docs:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- tracked config:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `config/applicability_adjudications/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`
- generated evidence surfaces:
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/`,
  `source_library/catalog/`,
  `source_library/derived/source-set-5e65d845ce77e1a0/`,
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/`
- source and tests if implementation is needed:
  `src/usfs_r1_ea_sources/replay_context.py`,
  `src/usfs_r1_ea_sources/catalog_surface.py`,
  `src/usfs_r1_ea_sources/phase_eval.py`,
  `tests/test_phase_eval.py`,
  focused applicability, component, and v1 eval tests for any regenerated
  contract surface

## Placement Rules

- Keep source-set ownership declarative in tracked replay/eval config and
  governed generated artifacts.
- Do not add a Tyler's Kitchen special case to phase evaluation.
- Prefer local reuse/replay from governed catalogs and package cache before any
  downloader/network recapture.
- Commit only tracked docs, config, source, and tests; leave generated
  `source_library/` evidence ignored.
- Every readiness claim must cite `phase-eval` and `v1-ea-eval` readback, not a
  single passing subcommand.

## Weak-Point Prevention Contract

| Milestone | Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse prevented |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | A session silently treats `f70...` as a drop-in manifest for `5e65...` | replay context, catalog manifests, extraction manifests | source-record-set comparison plus replay-context readback | chosen owner has mismatched catalog/extraction source-record IDs and no regeneration plan | prove `5e65...` selected IDs differ from `f70...` catalog IDs before choosing owner | fake currentness by swapping only a manifest path |
| `1` | Local replay regenerates only one artifact family and leaves mixed source-set outputs | tracked config, applicability, component, compliance review artifacts | governed command chain plus `phase-eval` readback | any review-local artifact still advertises the old source set after rebaseline | stale review-local artifact fixture must fail `phase-eval` | mixed `5e65...` and current-workbook artifacts hidden by prose |
| `2` | Direct-eval rebaseline starts before source-register currentness is coherent | parent aligned-runtime packet and direct-eval results | `phase-eval` source-register phase must be green or an exact narrower stop opened | `source_register_contract` remains red while retrieval/rule-claim work is claimed current | preserve red direct-eval phases in closeout until source-register phase is green | losing the active blocker behind direct-eval work |
| `3` | Closeout claims Lolo is ready or changes roster semantics without aggregate proof | coverage and promotion configs/docs | `v1-ea-eval`, `phase-eval`, coverage and promotion readback if roster changes are proposed | Lolo is added to governed roster while review phase-eval is red | aggregate gates fail closed on missing/incorrect slot state | accidental promotion from example-package wording |

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Current-workbook owner choice rebaseline | `reduced` |
| `1` | Governed local replay or exact local-replay stop | `reduced` |
| `2` | Source-register phase closure and direct-eval handoff | `resolved` |
| `3` | Exact closeout route and docs alignment | `resolved` |

### Milestone 0 - Current-Workbook Owner Choice Rebaseline

Outcome label: reduced

Closeout status: complete locally after commit. The owner-choice gate selected
the governed replay/exact-stop path and ruled out a silent `f70...` manifest
swap.

Purpose: choose the smallest valid current-workbook owner path before any
artifact regeneration.

Implementation:

1. Compare the tracked `5e65...` extraction manifest source-record IDs, the
   current active catalog, and the current-workbook `f70...` archived catalog.
2. Decide whether Lolo should replay against `f70...`, a new current-workbook
   catalog gate, or an explicitly narrower blocker.
3. Update this plan and current-route docs with the chosen owner and command
   chain.

Acceptance criteria:

- The selected owner has a source-record compatibility proof or a regeneration
  plan that explains every required artifact family.
- `source_register_contract` is not bypassed.
- No ignored generated JSON is hand-edited.
- Active routing names Milestone 1 as the next live slice and keeps `f70...`
  out of drop-in manifest wording.

Milestone 0 decision:

- `source-set-f70ea11e04ae3d53` remains the only current-workbook archived
  catalog gate found locally, but it is not source-record compatible with the
  historical `5e65...` review artifacts.
- The next live slice is Milestone 1. Start with the smallest governed local
  replay path that can bind Lolo to a current-workbook owner and prove
  source-record identity compatibility across applicability, forest-plan
  component eval, compliance review, and direct eval surfaces.
- If that replay path cannot reconcile the `R1EA-*` versus `FED-*`
  source-record identity split without downloader/corpus recapture, stop and
  open a narrower source-record identity or catalog-currentness blocker.

Verification:

```bash
PYTHONPATH=src python - <<'PY'
from pathlib import Path
from usfs_r1_ea_sources.catalog_surface import catalog_source_record_ids
from usfs_r1_ea_sources.catalog_surface import selected_source_record_ids_for_source_set

output_dir = Path("source_library")
ids_5e65 = selected_source_record_ids_for_source_set(
    output_dir=output_dir,
    source_set_id="source-set-5e65d845ce77e1a0",
) or set()
ids_f70 = catalog_source_record_ids(
    output_dir / "runs/current-source-gap-closeout-catalog-gate/catalog_gate"
) or set()
print({"5e65_selected": len(ids_5e65), "f70_catalog": len(ids_f70), "sets_equal": ids_5e65 == ids_f70})
PY

jq '{source_set_id,catalog_dir}' \
  config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json
```

### Milestone 1 - Governed Local Replay Or Exact Stop

Outcome label: reduced

Closeout status: reduced locally by exact stop to
`docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`;
no tracked replay context, eval contract, or ignored generated review artifact
was changed. The child identity gate follow-on is now complete in `dd3c322`
(`Resolve Lolo source-record identity gate`), and this packet should resume only
through that child packet's Milestone 2 replay-config route.

Purpose: regenerate the Lolo review against the chosen current-workbook owner, or
stop at the first artifact family that cannot be locally replayed without broad
download/corpus work.

Implementation:

1. Update tracked replay/eval config only after the owner choice is proven.
2. Run the smallest governed local replay chain for applicability,
   forest-plan component eval, compliance review, and `v1-ea-eval`.
3. Stop and open a narrower blocker if package cache, catalog compatibility, or
   extraction/retrieval prerequisites are missing.

Acceptance criteria:

- One exact stop condition is recorded: source-record identity must have a
  governed replay-facing owner before Lolo replay config can move from `5e65...`
  to `f70...`.
- `v1-ea-eval` and review `phase-eval` remain the required rerun gates after
  any later replay.
- No roster or threshold is weakened.

Milestone 1 decision:

- Direct CLI replay against `source-set-f70ea11e04ae3d53` stopped with
  `ReplayContextMismatchError` because the tracked Lolo replay context declares
  `source-set-5e65d845ce77e1a0`.
- The current-workbook catalog can explain most legacy expected IDs only through
  tracked reconciliation data: 8 expected IDs are direct current-catalog hits,
  51 absent expected IDs are mapped by the compliance source-record
  reconciliation, and `R1PLAN-lolo-nf-02` is mapped separately by the forest-plan
  identity reconciliation to `FPS-298`. The child identity gate has since
  resolved the five compliance-reconciled multi-target mappings with explicit
  governed identity selectors.
- The live next packet is
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
  before any runtime config or replay artifact moves to the current-workbook
  source set. That child packet has now completed Milestone 1 by implementing
  the replay-facing identity gate and making it green on the current
  `f70...` catalog; replay config movement now belongs to that child packet's
  Milestone 2.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344
```

### Milestone 2 - Source-Register Phase Closure And Direct-Eval Handoff

Outcome label: resolved

Closeout status: complete after this verified slice is committed. The child
source-record identity packet moved Lolo onto `source-set-f70ea11e04ae3d53` and
review `phase-eval` now passes `28/28`; `source_register_contract`,
`retrieval`, `rule_claim_binding`, `downstream_direct_evaluation`, and
`evaluation_coverage` are no longer red for this review on the current-workbook
owner.

Purpose: prove `source_register_contract` is no longer the active blocker before
resuming parent aligned-runtime direct-eval rebaseline.

Implementation:

1. Rerun `phase-eval` and inspect the `source_register_contract` phase details.
2. If the phase passes, route back to
   `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
   Milestone 2 for retrieval, rule-claim, and compliance direct-eval rebaseline.
3. If the phase still fails, open the exact narrower owner and stop.

Acceptance criteria:

- `source_register_contract` passes on `source-set-f70ea11e04ae3d53`.
- Direct-eval identity red is cleared for this review under the current
  `phase-eval` contract; review-scoped direct eval remains
  `not_required_for_ad_hoc_review`.
- No docs claim roster promotion until the broader Lolo example-package parent
  implements its registry/coverage threshold ratchet.

Verification:

```bash
jq '{review_id,source_set_id,passed,passed_phase_count,phase_count,failed_phase_names:[.phases[]|select(.passed==false)|.name],source_register:[.phases[]|select(.name=="source_register_contract")][0]}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json
```

### Milestone 3 - Exact Closeout Route And Docs Alignment

Outcome label: resolved

Closeout status: complete after this verified slice is committed. The next
owner is the broader
`docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` Milestone 3
registry promotion, threshold ratchet, and queue reroute. This current-workbook
source-set packet is no longer active.

Purpose: close this packet with one precise next owner.

Implementation:

1. Update current routing, current-state, handoff, parent plans, and promotion
   notes to match the verified state.
2. Run plan lint and focused verification for touched behavior/config surfaces.
3. Stage and commit only the verified slice.

Acceptance criteria:

- Active docs name exactly one next packet or the parent aligned-runtime return.
- The handoff records verification, skipped checks, and residual risk.
- The worktree is clean after commit.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md

git diff --check
```

## Required Implementation Artifacts

- this current-workbook source-set rebaseline plan
- `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- any focused replay-context, eval-contract, source, or test changes selected by
  the milestone owner choice
- updated current-routing and handoff docs
- ignored generated evidence from governed commands, kept out of git

## Required Documentation And Handoff Updates

- `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/AGENT_START_HERE.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`
- `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- this plan

## Required Verification Gates

- strict milestone-plan lint for this plan and any touched milestone plan docs
- exact source-record-set comparison for owner choice
- `v1-ea-eval` and review `phase-eval` after any replay/config change
- focused tests for any touched source/config behavior
- `git diff --check`

## Acceptance Criteria

- The active Lolo owner is current-workbook grounded and testable.
- Historical `5e65...` artifacts are not treated as current without a matching
  manifest/currentness surface.
- The source-register workbook SHA contract remains enforced.
- Governed roster and promotion semantics remain unchanged unless a later
  verified gate proves `phase-eval` and roster coverage pass.

## Stop Conditions

- Stop if the only path is to hand-edit ignored generated JSON.
- Stop if local replay cannot proceed without network/download recapture; open a
  downloader/catalog rebuild packet instead.
- Stop if any fix would make `source_register_contract` optional.
- Stop if Lolo would need roster admission before review `phase-eval` is green.

## Local Commit Closeout Policy

- `complete-after-commit` rule: a milestone is not complete until verification
  passes, durable docs/handoff updates land, and the local atomic commit
  exists. A verified but uncommitted slice is ready-to-close only.
- Stage only the verified tracked slice for this blocker.
- Leave ignored `source_library/` runtime evidence local.
- Include this plan, touched routing docs, focused source/config/test changes,
  and handoff updates in the same milestone commit.
- Preserve anti-test-weakening rules: do not weaken tests or gates; do not
  skip, xfail, loosen, or narrow gates to clear source-register or direct-eval
  red.

## Residual Risks And Next Milestone Routing

- The current-workbook owner is not a manifest swap and not an ad hoc CLI
  override. It is the tracked Lolo replay context plus eval/adjudication config
  on `source-set-f70ea11e04ae3d53`, backed by the source-record identity gate
  and final `v1-ea-eval` / `phase-eval` readback.
- The remaining work is not source-register currentness or source-record
  identity. The next owner is the broader Lolo example-package parent if the
  user wants to promote `lolo-nf` from `profile_eval_guidance_only` to
  `real_package_examples_available`.
- That future promotion must update registry and aggregate coverage configs and
  rerun the governed aggregate gates. This packet does not change roster,
  promotion-suite, or forest-specific example registry semantics.
