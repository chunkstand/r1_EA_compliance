# Lolo Tyler's Kitchen Aligned Runtime Rebaseline Blocker Milestone Plan

Date: 2026-05-26

Status: Reduced locally through Milestone 1 (`review-local applicability companion
artifacts and forest-plan component eval are now green on source-set-5e65d845ce77e1a0;
the source-register currentness child stopped to
docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md
because no exact current 5e65 manifest exists before this packet can continue to
direct-eval rebaseline`)

Owner context: standalone child packet opened after
`docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
resolved exact child-route closeout. The tracked Lolo review
`region1-example-lolo-tylers-kitchen-66344` no longer has a source-set contract split:
the replay context and tracked `v1-ea-eval` contract now both bind to
`source-set-5e65d845ce77e1a0`, and fresh `v1-ea-eval` is already
`contract_status="reviewer_ready"`. At packet open, the remaining review-bound blocker
spanned stale direct-eval lanes, stale review-local applicability validation companions,
a stale forest-plan component eval contract, and a `source_register_contract` phase that
still fell back to the global catalog manifest on `4fb...`. Milestone 1 reduced the
review-local family, leaving stale direct-eval identity/quality drift plus the
source-register currentness child route. This packet owns that aligned-runtime
rebaseline family only. It does not reopen the broader Tyler's Kitchen package-authority
lane, current promotion, ECID historical slot semantics, or a full canonical rebuild
unless a later milestone proves the source-register dependency cannot be resolved inside
a narrower boundary.

Opening closeout commit:
`a7b4141` (`Open Lolo aligned runtime rebaseline blocker`)

## Latest Local Implementation

- This packet is now the exact live child route after source-set contract blocker
  Milestone 3 closeout in `a7b4141`
  (`Open Lolo aligned runtime rebaseline blocker`).
- Milestone 0 freshness inventory is resolved locally. No runtime reruns were executed
  during this lock; the slice only re-read tracked contracts plus live ignored artifacts
  and froze the exact stale-surface family before Milestone 1.
- Milestone 1 review-local artifact rebaseline is reduced locally. The governed
  applicability chain was refreshed on `source-set-5e65d845ce77e1a0`, the existing
  four-item Lolo applicability adjudication was replayed against the refreshed decision
  hash, `applicability-validate` and `applicability-generate-rule-pack` now pass, and
  `forest-plan-component-eval` now passes after the tracked eval contract moved to
  `5e65...`.
- Fresh readback proves one coherent narrower owner family:
  - `phase_eval_results.json` is now red at `18/23` on
    `source-set-5e65d845ce77e1a0`, not on the older tracked `4fb...` contract.
  - `retrieval_eval_results.json` already exists on `5e65...`, but its recorded
    contract SHA is `3ea1...` while `config/retrieval_eval_seed.json` now hashes to
    `394aa7...`; the existing result is also semantically red with failed cases
    `nepa-alternatives-environmental-effects` and `scoping-public-comment`, plus
    false-positive, missing-source, recall, MRR, and NDCG threshold misses.
  - `rule_claim_link_eval_results.json` already exists on `5e65...`, but its recorded
    contract SHA is `34faf3...` while `config/rule_claim_link_eval_seed.json` now
    hashes to `59bce8...`; its cases and metric checks otherwise pass.
  - `compliance_review_eval_results.json` still passes only on
    `source-set-f70ea11e04ae3d53`, so `downstream_direct_evaluation` remains stale on the
    aligned Lolo owner path.
  - `authority_universe_snapshot.json`, `applicability_validation.json`,
    `generated_rule_pack_validation.json`, and `forest_plan_component_eval_results.json`
    now all pass on `5e65...`.
  - `source_register_contract` is the one possibly broader surface: the review replay
    context carries no review-local source manifest path or workbook path, so
    `phase-eval` currently compares the active workbook hash
    `1b62348930fa9c3595bea24b6ab4cfa4c7b0a3d2c29c1f1cfefebcf9d270cf97` against the
    global `source_library/catalog/source_set_manifest.json`, which still declares
    `source-set-4fb59e9eb43045cb` and workbook SHA
    `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`.
- Live work now moves to the source-register currentness child packet:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`.
  That child has now stopped to the broader current-workbook source-set
  rebaseline packet:
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`.
  The current-workbook packet is reduced locally through Milestone 0: the
  `f70...` catalog gate is not a drop-in owner for the historical `5e65...`
  review artifacts because source-record identity differs. Its next slice is
  Milestone 1 governed local replay or exact local-replay stop.
  This packet should resume at Milestone 2 direct-eval rebaseline only after
  the current-workbook source-set owner is rebuilt or selected and
  `source_register_contract` is no longer the active blocker.

## Purpose

Rebaseline the aligned Lolo runtime family after source-set contract alignment.

The tracked replay context and tracked `v1-ea-eval` contract are no longer the blocker.
The remaining red is now one narrower family:

- direct-eval artifacts on the aligned `5e65...` path are stale against current shipped
  eval contracts;
- one downstream direct-eval lane still points at shared `f70...` coverage; and
- one review-bound phase still falls back to the global source-set manifest rather than a
  review-local source-register surface.

This packet exists to refresh or classify those exact runtime surfaces without pretending
the older source-set contract split is still live.

Freshness check rule:
before any reruns begin, re-read `docs/CURRENT_ROUTING.md`,
`docs/CURRENT_SYSTEM_STATE.md`, the top of `docs/SESSION_HANDOFF.md`,
`config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
`config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
`config/retrieval_eval_seed.json`,
`config/rule_claim_link_eval_seed.json`,
`config/compliance_review_eval_seed.json`,
`config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`,
the live `source_library/catalog/source_set_manifest.json`,
`source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`,
`source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/authority_universe_snapshot.json`,
`source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/generated_rule_pack_validation.json`,
`source_library/reviews/region1-example-lolo-tylers-kitchen-66344/forest_plan_component_eval_results.json`,
and the current direct-eval result files on `5e65...` plus the shared
`compliance_review_eval_results.json`. If the source-set IDs, workbook SHA, eval contract
SHAs, or governed aggregate routing drift, update this packet and the live routing docs
before implementation continues.

## Current Evidence

- `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and the top of
  `docs/SESSION_HANDOFF.md` now route the remaining tracked Lolo blocker through this
  aligned-runtime rebaseline packet, with
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
  preserved as the exact predecessor that resolved the tracked source-set
  contract split.
- The tracked replay context
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
  now declares `source_set_id="source-set-5e65d845ce77e1a0"`.
- The tracked `v1-ea-eval` contract
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`
  now also declares `source_set_id="source-set-5e65d845ce77e1a0"`.
- The live review result
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`
  now reports `contract_status="reviewer_ready"`, `passed=true`,
  `broader_ea_passed=true`, and `forest_plan_passed=true` on
  `source-set-5e65d845ce77e1a0`.
- The live review phase result
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`
  now reports `passed=false`, `passed_phase_count=18/23`, and failing phases
  `retrieval`, `rule_claim_binding`, `downstream_direct_evaluation`,
  `source_register_contract`, and `evaluation_coverage`.
- The stale direct-eval family is exact:
  - `source_library/derived/source-set-5e65d845ce77e1a0/retrieval/retrieval_eval_results.json`
    still records `actual_contract_sha256=3ea1...`, while the current
    `config/retrieval_eval_seed.json` expects `394aa7...`; the existing result also still
    fails case and metric checks (`eval_cases_pass=false`,
    `metric_thresholds_met=false`).
  - `source_library/derived/source-set-5e65d845ce77e1a0/rule_claim_links/nepa-ea-v0/0.4.0/rule_claim_link_eval_results.json`
    still records `actual_contract_sha256=34faf3...`, while the current
    `config/rule_claim_link_eval_seed.json` expects `59bce8...`; the existing cases and
    metrics pass, but the contract is stale.
  - `source_library/reviews/compliance_review_eval/compliance_review_eval_results.json`
    still records `actual_source_set_id="source-set-f70ea11e04ae3d53"` even though
    `phase-eval` now expects `5e65...` for this review.
- The review-local contract family is now reduced:
  - `applicability-authority-universe` now passes on `5e65...` with
    `candidate_authority_count=396` and `forest_plan_component_candidate_count=329`.
  - The refreshed applicability decision pass covers all `396` candidates; the existing
    four-item Lolo applicability adjudication was replayed, leaving
    `needs_adjudication_authority_count=0`.
  - `applicability_validation.json` now passes on `5e65...` with
    `generated_rule_pack_ready=true`.
  - `generated_rule_pack_validation.json` now declares `5e65...` and passes with
    `generated_rule_count=54`.
  - `forest_plan_component_eval_results.json` now passes after the tracked eval contract
    declared `source_set_id="source-set-5e65d845ce77e1a0"`.
- `source_register_contract` is currently the only potentially broader stop:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
  carries no review-local `source_manifest_path` or workbook path, and
  `review_validation.json` carries no workbook/source-manifest identity either, so
  `phase-eval` currently falls back to the global
  `source_library/catalog/source_set_manifest.json`. That manifest still declares
  `source_set_id="source-set-4fb59e9eb43045cb"` with
  `workbook_sha256="2c511784..."`, while the current workbook on disk hashes to
  `1b623489...`.
- Governed aggregates remain unchanged. `real-package-review-coverage-eval` still admits
  only East Crazies, West Reservoir, and South Plateau, non-strict
  `promotion-suite` remains green for current promotion, and strict expansion remains red
  only on the ECID historical slot under `historical_source_set_split`.

## Goal

Leave the repository with one exact aligned-runtime owner outcome for the tracked Lolo
review:

- either the stale aligned-runtime artifacts and direct-eval contracts are refreshed on
  the chosen `5e65...` path and the remaining red shrinks to one still narrower semantic
  owner; or
- one explicit narrower stop condition is recorded if the source-register or direct-eval
  family cannot be resolved inside this packet without broadening scope.

Completion means all of the following are true:

- current-facing docs no longer present the remaining Lolo blocker as source-set contract
  drift;
- the exact stale aligned-runtime surfaces are enumerated from tracked configs, direct-eval
  results, review-local validation artifacts, and phase-eval readback together;
- no governed roster, slot-floor, or ready-state contract is weakened; and
- the next owner after this packet, or the exact stop condition inside it, is named
  explicitly in tracked docs and handoff.

## Non-Goals

- Do not flip the ECID historical slot to `ready`, delete it, or lower the governed
  expansion floor.
- Do not admit the tracked Lolo review into
  `config/v1_real_package_review_coverage_v1.json` or
  `config/promotion_suite_v1.json` while `phase-eval` remains red.
- Do not reopen the broader Tyler's Kitchen package-authority and forest-registry lane in
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`.
- Do not manually patch ignored `source_library/` JSON to force source-set, contract, or
  workbook agreement.
- Do not widen this packet into downloader, catalog rebuild, or full canonical source-set
  recreation unless Milestone 1 proves `source_register_contract` cannot be owned more
  narrowly.

## Scope

- aligned runtime surfaces for `region1-example-lolo-tylers-kitchen-66344`
- stale direct-eval contracts and result files needed by review-bound `phase-eval`
- stale review-local applicability companion artifacts on the aligned owner path
- the tracked forest-plan component eval contract for this review
- the review-bound `source_register_contract` fallback only as needed to decide whether it
  stays in-scope here or stops to another owner
- current-routing and lineage docs for the exact live blocker route

## Out Of Scope

- broader Tyler's Kitchen package intake or queue routing
- ECID slot semantics, manifest-floor redesign, or current-promotion reroute
- broad catalog/source-set rebuild work beyond an exact stop condition
- unrelated Lolo queue, Pinyon, or forest-profile backlog work

## Owner Surfaces

- live blocker docs:
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/AGENT_START_HERE.md`
- preserved predecessor and lineage docs:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- tracked config and contract surfaces:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `config/retrieval_eval_seed.json`,
  `config/rule_claim_link_eval_seed.json`,
  `config/compliance_review_eval_seed.json`,
  `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`,
  `source_library/catalog/source_set_manifest.json`
- live ignored runtime outputs:
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`,
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/authority_universe_snapshot.json`,
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/generated_rule_pack_validation.json`,
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/forest_plan_component_eval_results.json`,
  `source_library/derived/source-set-5e65d845ce77e1a0/retrieval/retrieval_eval_results.json`,
  `source_library/derived/source-set-5e65d845ce77e1a0/rule_claim_links/nepa-ea-v0/0.4.0/rule_claim_link_eval_results.json`,
  `source_library/reviews/compliance_review_eval/compliance_review_eval_results.json`
- command owners and focused tests if code or contract changes become necessary:
  `src/usfs_r1_ea_sources/phase_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval_source_set_phases.py`,
  `src/usfs_r1_ea_sources/phase_eval_review_phases.py`,
  `src/usfs_r1_ea_sources/applicability.py`,
  `src/usfs_r1_ea_sources/applicability_rule_pack.py`,
  `src/usfs_r1_ea_sources/retrieval_eval_runtime.py`,
  `src/usfs_r1_ea_sources/rule_claim_binding_eval.py`,
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  `src/usfs_r1_ea_sources/forest_plan_component_eval_runtime.py`,
  `tests/test_phase_eval.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_retrieval_eval.py`,
  `tests/test_rule_claim_binding_eval.py`,
  `tests/test_applicability_rule_pack.py`,
  `tests/test_forest_plan_component_eval.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_promotion_suite.py`,
  `tests/test_cli_eval.py`

## Placement Rules

- Keep source-set truth declarative in tracked replay contexts, eval contracts, shipped eval
  seeds, and review-local validation artifacts. Do not hide alignment fixes in ad hoc runtime
  branches.
- Keep canonical source-set direct-eval truth on the source-set-owned output files. Do not
  repoint `retrieval-eval`, `rule-claim-eval`, or `compliance-review-eval` at manual
  review-local substitutes just to satisfy `phase-eval`.
- Keep review-local applicability companion artifacts (`authority_universe_snapshot.json`
  and `generated_rule_pack_validation.json`) generated by their governed commands rather than
  hand-edited patches.
- Keep the forest-plan component eval contract declarative in
  `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`.
- If `source_register_contract` still requires a broader currentness/catalog manifest owner,
  stop and open that narrower packet instead of widening this packet silently.
- Keep ignored runtime evidence under `source_library/`; commit only tracked docs, config,
  code, and tests.

## Weak-Point Prevention Contract

| Milestone | Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse prevented |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | A later session starts reruns from stale assumptions and mixes `4fb...`, `5e65...`, and `f70...` surfaces again | this plan, current-route docs, tracked config, live artifact readback | exact `jq` inventory over the tracked config and live artifact family before reruns | the current packet does not enumerate the stale direct-eval, stale review-local, and broader source-register surfaces explicitly before implementation | re-read one stale artifact from each family (`retrieval_eval_results.json`, `generated_rule_pack_validation.json`, `source_set_manifest.json`) and fail if any are omitted from the packet | a future session reruns one command and claims the whole blocker moved without proving the exact stale family |
| `1` | Review-local artifact refresh is faked by editing JSON or by rerunning only one companion file while leaving the others stale | applicability companion artifacts, forest-plan component eval contract, source-register fallback | governed command reruns plus phase-eval readback | `authority_universe` or `generated_rule_pack` still fail `source_set_matches`, `forest_plan_component_eval` still fails only on `review_identity_matches_contract`, or `source_register_contract` still falls back to the global `4fb...` manifest without an explicit stop | rerun `applicability-authority-universe`, `applicability-generate-rule-pack`, and `forest-plan-component-eval`; phase-eval must observe the resulting identity changes | a future session edits the eval file or validation JSON by hand and skips the actual generator command |
| `2` | Direct-eval identity drift is cleared superficially while retrieval quality still stays semantically red | retrieval, rule-claim, and compliance-review direct-eval surfaces | fresh direct-eval reruns plus `phase-eval` and `v1-ea-eval` readback | `retrieval`, `rule_claim_binding`, or `evaluation_coverage` still report direct-eval identity mismatch after reruns; or retrieval still fails semantically and no narrower child is opened | rerun `retrieval-eval`, `rule-claim-eval`, and `compliance-review-eval`, then require `phase-eval` readback to distinguish stale-contract closure from remaining semantic red | a future session treats any fresh eval file as success even if retrieval still fails cases or thresholds |
| `3` | Closeout routes the blocker incorrectly or claims ready replacement while only rebaseline debt moved | current-state docs, handoff, promotion/coverage aggregates | targeted doc readback, `real-package-review-coverage-eval`, `promotion-suite`, `git diff --check` | docs still present source-set contract drift as the active blocker, or Lolo is implicitly treated as ready before `phase-eval` is green | keep the aggregate readback in the closeout bundle and require the next owner or explicit stop to be named | a future session closes the wrong packet because `v1-ea-eval` is already green |

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Freshness lock and exact aligned-runtime inventory | `resolved` |
| `1` | Review-local contract artifact rebaseline | `reduced` |
| `2` | Aligned direct-eval rebaseline and phase-eval reclassification | `reduced` |
| `3` | Exact child-route or readiness-stop closeout | `resolved` |

### Milestone 0 - Freshness lock and exact aligned-runtime inventory

Outcome label: resolved

Purpose: prove the exact stale aligned-runtime family before any reruns begin.

Implementation:

1. Re-read the tracked replay context, tracked `v1-ea-eval` contract, current source-set
   manifest, current `phase_eval_results.json`, the aligned `5e65...` direct-eval result
   files, the shared `compliance_review_eval_results.json`, and the review-local
   applicability/component validation artifacts together.
2. Record which surfaces are stale only by contract identity, which are stale and also
   semantically failing, and which one surfaces (`source_register_contract`) may already
   escape review-local scope.
3. Update this packet and the current route docs before any reruns if those surfaces drift.

Acceptance criteria:

- Milestone 0 exits with one explicit inventory of stale aligned-runtime surfaces.
- The packet distinguishes review-local artifact drift from source-set direct-eval drift and
  from the broader source-register fallback.
- No rerun claims land without that inventory.

Verification:

```bash
jq '{review_id,source_set_id,catalog_dir,source_manifest_path,workbook_path,package_path}' \
  config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json

jq '{review_id,source_set_id,passed,contract_status,broader_ea_passed,forest_plan_passed}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json

jq '{review_id,source_set_id,passed,passed_phase_count,phase_count,failed_phase_names:[.phases[]|select(.passed==false)|.name]}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json

jq '{source_set_id,workbook_path,workbook_sha256}' \
  source_library/catalog/source_set_manifest.json

jq '{review_id,source_set_id,created_at,summary}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/authority_universe_snapshot.json

jq '{review_id,source_set_id,created_at,summary}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/generated_rule_pack_validation.json

jq '{review_id,source_set_id,created_at,checks}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/forest_plan_component_eval_results.json

jq '{summary:.summary}' \
  source_library/derived/source-set-5e65d845ce77e1a0/retrieval/retrieval_eval_results.json

jq '{summary:.summary}' \
  source_library/derived/source-set-5e65d845ce77e1a0/rule_claim_links/nepa-ea-v0/0.4.0/rule_claim_link_eval_results.json

jq '{checks:[.checks[]|{name,passed,details}]}' \
  source_library/reviews/compliance_review_eval/compliance_review_eval_results.json
```

### Milestone 1 - Review-Local Contract Artifact Rebaseline

Outcome label: reduced

Purpose: refresh the aligned review-local contract artifacts and classify whether
`source_register_contract` can stay in-scope here.

Implementation:

1. Rerun the aligned review-local applicability companion chain on `5e65...`:
   `applicability-authority-universe`, `applicability-validate`, and
   `applicability-generate-rule-pack`.
2. Refresh the tracked forest-plan component eval contract and rerun
   `forest-plan-component-eval` on the aligned owner path.
3. Re-read `phase-eval` and classify `source_register_contract` explicitly:
   - if a review-local manifest/currentness surface can be refreshed here, keep it in this
     packet;
   - if `phase-eval` still only sees the global `4fb...` manifest, stop and open the exact
     narrower manifest/currentness owner rather than broadening silently.

Acceptance criteria:

- `authority_universe` no longer fails only because `authority_universe_snapshot.json`
  advertises `4fb...`.
- `generated_rule_pack` no longer fails only because
  `generated_rule_pack_validation.json` advertises `4fb...`.
- `forest_plan_component_eval` no longer fails only because its tracked eval contract still
  advertises `4fb...`.
- `source_register_contract` either passes or exits this milestone with one exact narrower
  owner decision.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --eval-file config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344
```

### Milestone 2 - Aligned Direct-Eval Rebaseline And Phase-Eval Reclassification

Outcome label: reduced

Purpose: refresh the stale direct-eval family and prove whether any remaining red is now a
still narrower semantic owner.

Implementation:

1. Rerun `retrieval-eval` on `source-set-5e65d845ce77e1a0`.
2. Rerun `rule-claim-eval` on `source-set-5e65d845ce77e1a0`.
3. Rerun `compliance-review-eval` on `source-set-5e65d845ce77e1a0`.
4. Rerun `phase-eval`, then classify the remaining red:
   - if direct-eval identity mismatch is gone but retrieval remains semantically red, route
     to a narrower retrieval/rule-claim quality owner;
   - if all direct-eval gates are green, continue to Milestone 3 with the exact remaining
     owner or readiness proof.

Acceptance criteria:

- `retrieval`, `rule_claim_binding`, and `evaluation_coverage` no longer fail only on stale
  direct-eval identity.
- `downstream_direct_evaluation` no longer depends on a stale `f70...` compliance-review
  eval without an explicit narrower owner.
- Governed aggregates remain unchanged unless a stronger verified result is actually proven.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344

PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json

PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```

### Milestone 3 - Exact Child-Route Or Readiness-Stop Closeout

Outcome label: resolved

Purpose: close this aligned-runtime blocker with one exact next owner.

Implementation:

1. Update the current docs, handoff, and this plan with the exact next owner after the
   aligned-runtime reruns:
   - a narrower semantic retrieval/rule-claim owner if direct-eval freshness is fixed but
     retrieval quality remains red;
   - a narrower source-manifest/currentness owner if `source_register_contract` still cannot
     be refreshed inside this packet; or
   - a ready replacement-path packet only if `phase-eval` and governed aggregates support it.
2. Preserve the source-set contract blocker and older Lolo/ECID packets as historical
   lineage only.
3. Stage only the verified tracked docs, config, code, and tests for this packet and commit
   the slice atomically.

Acceptance criteria:

- Current-facing docs no longer leave the remaining Lolo blocker generic.
- This packet either routes to one named next packet or records one explicit stop condition.
- The handoff records the exact verification bundle and residual risks.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md

git diff --check
```

## Required Implementation Artifacts

- this blocker plan
- exact current-facing routing to this packet
- preserved predecessor and lineage docs
- one named child packet or one explicit stop condition before this packet closes

## Required Documentation And Handoff Updates

- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/AGENT_START_HERE.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
- `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
- `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- this plan

## Required Verification Gates

- plan lint for any touched milestone plan docs
- `git diff --check`
- Milestone 0 exact `jq` inventory over the tracked config and live aligned-runtime surfaces
- if Milestone 1 executes runtime refresh:
  `applicability-authority-universe`,
  `applicability-validate`,
  `applicability-generate-rule-pack`,
  `forest-plan-component-eval`,
  and review `phase-eval`
- if Milestone 2 executes direct-eval refresh:
  `retrieval-eval`,
  `rule-claim-eval`,
  `compliance-review-eval`,
  review `phase-eval`,
  `v1-ea-eval`,
  `real-package-review-coverage-eval`,
  and non-strict `promotion-suite`
- if code or tracked contract files change:
  focused pytest for the touched eval/phase/applicability/component owners plus the repo's
  stricter gate set for those surfaces

## Acceptance Criteria

- The repository no longer routes future sessions to source-set contract drift as the active
  Lolo blocker.
- The stale aligned-runtime surfaces are frozen in tracked docs and tied to one exact next
  owner decision.
- The governed expansion slot floor and fail-closed slot contract remain unchanged while
  routing this blocker.
- The next packet after this blocker, or the exact stop condition inside this packet, is
  named explicitly in tracked docs and handoff.

## Stop Conditions

- Stop if the only apparent way forward is to admit Lolo into the governed roster before
  `phase-eval` is green.
- Stop if `source_register_contract` still depends only on the global `4fb...`
  `source_set_manifest.json` and no review-local manifest/currentness surface exists here;
  in that case, open the narrower manifest/currentness blocker rather than broadening this
  packet.
- Stop if fresh direct-eval reruns remove identity drift but retrieval remains semantically
  red; in that case, open the narrower retrieval/rule-claim quality owner rather than
  keeping this packet generic.
- Stop if resolving the aligned runtime family would require broad downloader, catalog, or
  full-canonical rebuild work and no smaller owner can be named.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no milestone in this plan may be marked complete, `resolved`,
  or `reduced` until verification passes, durable docs/handoff updates land, and the local
  atomic commit exists. A verified but uncommitted slice is only ready-to-close.
- Stage only the verified tracked slice for this blocker packet.
- Leave unrelated dirty or untracked files alone.
- Keep ignored `source_library/` evidence local.
- Include this blocker plan, the touched routing docs, and any named child-packet file
  opened during closeout in the same commit.
- Record the exact verification bundle in `docs/SESSION_HANDOFF.md`.
- Preserve anti-test-weakening rules: do not weaken or loosen gates, skip checks, or lower
  the governed slot floor to make aligned runtime routing look green.

## Residual Risks And Next Milestone Routing

- The aligned runtime family is now the exact parent owner after source-set contract
  alignment; its live child route is source-register currentness before direct-eval
  rebaseline resumes here.
- The only broader surface already visible at packet open is `source_register_contract`,
  which still falls back to the global `4fb...` catalog manifest and older workbook SHA.
- Milestones 0 and 1 have now reduced this packet to direct-eval identity drift plus
  source-register currentness.
- The source-register currentness child stopped to a broader current-workbook
  source-set rebaseline packet. If that child resolves, this packet resumes at
  Milestone 2 to refresh retrieval, rule-claim, and compliance direct-eval artifacts.
- If the aligned runtime family refreshes cleanly and retrieval quality still remains red,
  the next owner should be a narrower retrieval/rule-claim quality packet rather than a
  return to generic Lolo contract or ECID replacement classification.
