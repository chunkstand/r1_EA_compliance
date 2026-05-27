# Lolo Tyler's Kitchen Source Register Currentness Blocker Milestone Plan

Date: 2026-05-26

Status: Resolved locally by broader stop (`Milestones 0-2 proved no exact current
source-set-5e65d845ce77e1a0 manifest/currentness surface exists; live work now routes to
docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`)

Owner context: standalone child packet opened from
`docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
Milestone 1. The tracked Lolo review
`region1-example-lolo-tylers-kitchen-66344` now has coherent review-local runtime
artifacts on `source-set-5e65d845ce77e1a0`: `authority_universe`,
`generated_rule_pack`, `applicability_validation`, and `forest_plan_component_eval`
are green. The remaining non-direct-eval blocker is narrower:
`source_register_contract` still compares the active workbook SHA
`1b62348930fa9c3595bea24b6ab4cfa4c7b0a3d2c29c1f1cfefebcf9d270cf97` against the
global catalog manifest SHA
`2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49` from
`source_library/catalog/source_set_manifest.json`, whose `source_set_id` is still
`source-set-4fb59e9eb43045cb`.

## Latest Local Implementation

- The parent aligned-runtime packet is reduced locally through Milestone 1.
- The governed review-local refresh ran through:
  `applicability-authority-universe`, `applicability-context-build`,
  `applicability-retrieve`, `applicability-determine`,
  `applicability-adjudication-eval`, `applicability-adjudication-apply`,
  `applicability-validate`, `applicability-generate-rule-pack`,
  `forest-plan-component-eval`, and `phase-eval`.
- `phase_eval_results.json` improved from `15/23` to `18/23`; the remaining failing
  phases are `retrieval`, `rule_claim_binding`, `downstream_direct_evaluation`,
  `source_register_contract`, and `evaluation_coverage`.
- `source_register_contract` is the stop condition that owns this packet. Direct-eval
  identity drift remains real, but it stays in the parent aligned-runtime packet until
  this source-register currentness owner is resolved or explicitly stopped.
- Milestones 0-2 are resolved locally by explicit stop. Exact readback found no
  current `source-set-5e65d845ce77e1a0` manifest under
  `source_library/runs/**/source_set_manifest.json`, the current active catalog
  manifest is still `source-set-4fb59e9eb43045cb` with workbook SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`, and
  the only current-workbook archived manifest found locally is
  `source-set-f70ea11e04ae3d53` at
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`.
- That `f70...` manifest is not a valid drop-in currentness owner for the
  `5e65...` review: `selected_source_record_ids_for_source_set("5e65...")`
  reports `350` selected IDs, the `f70...` catalog reports `708` IDs, and the
  sets differ. The historical `5e65...` authority-currentness report is also
  stale for source-register ownership because it was generated on
  `2026-05-11T00:40:55.190598Z` from
  `source_library/catalog/source_set_manifest.json` at SHA
  `77361eec5963677104bf06dabe3f3d2934bfb75eae18990532d6054ba58152eb`,
  and no local `source_set_manifest.json` currently has that hash.
- The live route is now
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`.
  This packet must not be reopened to hand-edit ignored manifests or to teach
  `phase-eval` to ignore workbook SHA drift.

## Purpose

Resolve or precisely route the Lolo review-bound source-register currentness mismatch
without broadening into a downloader, catalog rebuild, full canonical source-set
recreation, or manual patch of ignored manifest JSON.

`phase-eval` currently reads `catalog_dir/source_set_manifest.json` through the tracked
replay context. For this review, `catalog_dir` is `source_library/catalog`, so the
source-register phase sees the global `4fb...` manifest even though the replay context,
review artifacts, authority currentness, and review-local runtime outputs now use
`source-set-5e65d845ce77e1a0`.

## Current Evidence

- `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json` declares
  `source_set_id="source-set-5e65d845ce77e1a0"` and `catalog_dir="source_library/catalog"`;
  it does not provide an independent `source_manifest_path` or `workbook_path`.
- `src/usfs_r1_ea_sources/replay_context.py` derives `source_set_manifest_path` from
  `catalog_dir`, and validates optional manifest paths against that same derived path.
- `src/usfs_r1_ea_sources/phase_eval.py` reads
  `source_set_manifest_path = catalog_dir / "source_set_manifest.json"`.
- `src/usfs_r1_ea_sources/phase_eval_source_set_phases.py` fails
  `source_register_contract` when the active workbook SHA does not match
  `source_set_manifest["workbook_sha256"]`.
- `find source_library/runs -path '*source_set_manifest.json'` finds no exact
  archived manifest for `source-set-5e65d845ce77e1a0`.
- The `source-set-f70ea11e04ae3d53` manifest at
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_set_manifest.json`
  matches the current active workbook SHA
  `1b62348930fa9c3595bea24b6ab4cfa4c7b0a3d2c29c1f1cfefebcf9d270cf97`, but it is
  not source-set compatible with the `5e65...` derived artifacts:
  `5e65...` selected source-record IDs count `350`, while that archived
  `f70...` catalog has `708` source-record IDs.
- The `5e65...` authority-currentness report validates its own historical
  source-set identity, but its `inputs.source_set_manifest_sha256` is
  `77361eec5963677104bf06dabe3f3d2934bfb75eae18990532d6054ba58152eb`, which
  no local `source_set_manifest.json` currently matches.
- Fresh review `phase-eval --review-id region1-example-lolo-tylers-kitchen-66344`
  reports `passed_phase_count=18/23` and
  `source_register_contract.details.workbook_sha_matches_manifest=false`.

## Goal

Leave the repository with one exact source-register currentness owner outcome:

- either `phase-eval` uses a governed `5e65...` source-register manifest/currentness
  surface and `source_register_contract` passes without manual ignored-output edits; or
- the packet records one explicit stop condition proving that a broader catalog/currentness
  rebuild is required before the aligned-runtime direct-eval work can continue.

Completion means all of the following are true:

- the active docs no longer treat the Lolo blocker as review-local applicability drift;
- the source-register currentness owner is named and verified by artifact readback;
- no governed roster, promotion slot, strict-expansion floor, or direct-eval threshold is
  weakened; and
- the route back to the aligned-runtime direct-eval packet, or the broader stop, is explicit.

## Non-Goals

- Do not edit `source_library/catalog/source_set_manifest.json` or any ignored runtime JSON
  by hand to force a pass.
- Do not admit Lolo into `config/v1_real_package_review_coverage_v1.json` or
  `config/promotion_suite_v1.json`.
- Do not rebuild the full canonical corpus unless Milestone 0 proves there is no smaller
  source-register currentness owner.
- Do not change retrieval, rule-claim, or compliance direct-eval thresholds in this packet.
- Do not reopen the older source-set contract, replacement-feasibility, ECID historical,
  or broader Tyler's Kitchen example-package packets as live owners.

## Scope

- `source_register_contract` behavior for the tracked Lolo review
- replay-context catalog/manifest ownership as needed for source-register currentness
- source-set manifest/currentness artifact discovery for `source-set-5e65d845ce77e1a0`
- phase-eval readback and focused phase-eval tests
- current routing, current-state, handoff, and packet lineage docs

## Out Of Scope

- retrieval quality repair
- direct-eval seed or result refresh
- downloader/network capture
- full canonical catalog recreation unless recorded as the explicit stop
- governed promotion or expansion roster changes

## Owner Surfaces

- live blocker docs:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/AGENT_START_HERE.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`
- parent and lineage docs:
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- tracked config:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
- generated currentness/manifest surfaces:
  `source_library/catalog/source_set_manifest.json`,
  `source_library/runs/**/source_set_manifest.json`,
  `source_library/derived/source-set-5e65d845ce77e1a0/authority_currentness/authority_currentness_report.json`,
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`
- source and tests if implementation is needed:
  `src/usfs_r1_ea_sources/replay_context.py`,
  `src/usfs_r1_ea_sources/catalog_surface.py`,
  `src/usfs_r1_ea_sources/phase_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval_source_set_phases.py`,
  `tests/test_phase_eval.py`

## Placement Rules

- Keep source-register currentness declarative in governed catalog/currentness surfaces or
  tracked replay context contracts. Do not hide a Lolo-specific branch in phase evaluation.
- If code changes are required, make the source-register manifest/currentness path generic
  for any replay-context review, not Tyler's Kitchen specific.
- Keep ignored `source_library/` evidence local; commit only tracked docs, config, source,
  and tests.
- Preserve `source_library/catalog` as the active global catalog unless a governed command
  creates or selects a narrower catalog surface.
- Treat direct-eval failures as separate remaining work after this packet; do not weaken
  them to make this source-register packet look green.

## Weak-Point Prevention Contract

| Milestone | Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse prevented |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | A session guesses the manifest owner and patches ignored JSON | replay context, manifest readback, phase-eval result | exact readback of replay context, all source-set manifests, phase source-register details, and phase-eval source code | no exact currentness owner or stop condition is named before edits | prove no exact `5e65...` manifest is available before choosing an implementation route | manually editing `source_library/catalog/source_set_manifest.json` |
| `1` | The source-register phase is made to pass by ignoring workbook SHA drift | phase-eval source-register phase and tests | focused unit test plus live `phase-eval` readback | `source_register_contract` passes without validating the active workbook contract or a governed currentness artifact | stale manifest/workbook SHA fixture must fail | weakening currentness semantics to clear a red phase |
| `2` | Closeout skips the direct-eval red that remains after currentness is fixed | current docs, handoff, parent aligned-runtime plan | `phase-eval` readback plus docs grep for active route | docs claim Lolo is ready or route to promotion before direct-eval gates are green | keep failed direct-eval phases in the closeout bundle | losing the remaining retrieval/rule-claim owner after this child closes |

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Source-register manifest/currentness owner rebaseline | `reduced` |
| `1` | Smallest currentness-owner implementation or explicit broad-rebuild stop | `reduced` |
| `2` | Route back to aligned direct-eval owner or record broader stop | `resolved` |

### Milestone 0 - Source-Register Manifest/Currentness Owner Rebaseline

Outcome label: reduced

Purpose: prove the exact owner of the `source_register_contract` failure before editing
code or config.

Implementation:

1. Re-read the tracked replay context, active global `source_set_manifest.json`, every
   archived `source_set_manifest.json`, the `5e65...` authority-currentness report, and
   the live review `phase_eval_results.json`.
2. Decide whether a governed exact `5e65...` manifest/currentness surface already exists.
3. If no exact surface exists, choose whether Milestone 1 should implement a generic
   replay-context manifest/currentness owner or stop to a broader catalog/currentness rebuild.

Acceptance criteria:

- The packet records whether any exact `5e65...` manifest exists.
- The packet names the smallest next owner and its verification gate.
- No ignored manifest JSON is edited by hand.

Verification:

```bash
jq '{source_set_id,catalog_dir,source_set_manifest_path,source_manifest_path,workbook_path}' \
  config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json

find source_library/runs -path '*source_set_manifest.json' -print

jq '{source_set_id,workbook_path,workbook_sha256,source_count,created_at}' \
  source_library/catalog/source_set_manifest.json

jq '{source_set_id,summary:{source_set_id:.summary.source_set_id,inventory_summary:.summary.inventory_summary}}' \
  source_library/derived/source-set-5e65d845ce77e1a0/authority_currentness/authority_currentness_report.json

jq '{review_id,source_set_id,passed,passed_phase_count,phase_count,failed_phase_names:[.phases[]|select(.passed==false)|.name],source_register:[.phases[]|select(.name=="source_register_contract")][0]}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json
```

### Milestone 1 - Smallest Currentness-Owner Implementation Or Stop

Outcome label: reduced

Purpose: make `source_register_contract` use a governed currentness source for the
aligned `5e65...` review, or record why this requires a broader catalog/currentness rebuild.

Implementation:

1. Prefer an existing governed command path if it can create or select an exact `5e65...`
   catalog/currentness manifest without network recapture.
2. If code is required, add a generic replay-context/currentness path that preserves the
   active workbook validation and workbook SHA check.
3. Add or update focused `tests/test_phase_eval.py` coverage for stale manifest failure and
   current manifest/currentness success.
4. Rerun review `phase-eval` and classify the remaining red.

Acceptance criteria:

- `source_register_contract` either passes on the aligned Lolo review or exits with a
  documented broader rebuild stop.
- If it passes, the details still show the active workbook exists, validates, and matches
  the governed currentness SHA.
- No direct-eval failure is hidden or downgraded.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval.py -q

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344
```

### Milestone 2 - Route Back Or Record Broader Stop

Outcome label: resolved

Purpose: close this child packet with a precise next owner.

Implementation:

1. If `source_register_contract` passes, route back to the parent aligned-runtime packet at
   direct-eval rebaseline and preserve the remaining failed phases.
2. If a broader catalog/currentness rebuild is required, open that exact packet and stop.
3. Update current docs, handoff, and parent packet lineage. Commit only the verified slice.

Acceptance criteria:

- Active docs name exactly one next packet or stop condition.
- Lolo is not claimed as ready while `phase-eval` remains red.
- The verification bundle is recorded in `docs/SESSION_HANDOFF.md`.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md

git diff --check
```

## Required Implementation Artifacts

- this source-register currentness blocker plan
- any focused replay-context, phase-eval, or catalog/currentness implementation needed by
  Milestone 1
- focused tests for the chosen currentness owner
- updated current-routing and handoff docs

## Required Documentation And Handoff Updates

- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/AGENT_START_HERE.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- this plan

## Required Verification Gates

- strict milestone-plan lint for this plan and any touched milestone plan docs
- exact readback of replay context, manifest/currentness sources, and phase-eval
- `PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval.py -q` if code or phase
  contract behavior changes
- review `phase-eval` for `region1-example-lolo-tylers-kitchen-66344`
- `git diff --check`

## Acceptance Criteria

- The active source-register currentness owner is explicit and testable.
- No ignored source-library manifest is manually patched.
- The active workbook contract stays validated; workbook SHA drift is not ignored.
- The parent aligned-runtime packet can resume at direct-eval rebaseline only after the
  source-register currentness owner is resolved or stopped.

## Stop Conditions

- Stop if the only way to pass `source_register_contract` is to hand-edit ignored
  `source_library/` JSON.
- Stop if a full catalog/source-set rebuild is required; open a broader catalog/currentness
  rebuild packet instead of silently broadening this child.
- Stop if any proposed fix would make `source_register_contract` optional for canonical
  source-register contexts.
- Stop if Lolo would need to be admitted into the governed roster before `phase-eval` is
  green.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no milestone in this plan may be marked complete,
  `resolved`, or `reduced` until verification passes, durable docs/handoff updates land,
  and the local atomic commit exists. A verified but uncommitted slice is only
  ready-to-close.
- Stage only the verified tracked slice for this blocker.
- Leave ignored `source_library/` runtime evidence local.
- Include this plan, touched routing docs, focused source/config/test changes, and handoff
  updates in the same milestone commit.
- Preserve anti-test-weakening rules: do not skip, xfail, loosen, or narrow gates to clear
  `source_register_contract`.

## Residual Risks And Next Milestone Routing

- This packet starts because the aligned-runtime Milestone 1 refresh proved review-local
  applicability and forest-plan component artifacts are no longer the current blocker.
- The remaining direct-eval failures are still real and should return to the parent
  aligned-runtime packet after source-register currentness is resolved.
- Source-register currentness required broader owner rebaseline. The next active packet is
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  and the parent direct-eval work stays paused.
