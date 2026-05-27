# Lolo Tyler's Kitchen Source-Set Contract Blocker Milestone Plan

Date: 2026-05-26

Status: Historical resolved predecessor packet (`Milestones 1-3 are now resolved
locally; the tracked replay context and review eval contract align to
source-set-5e65d845ce77e1a0, and the exact live work now routes to the aligned runtime
rebaseline blocker`)

Owner context: standalone follow-on opened after
`docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
proved that the tracked Lolo replacement path no longer has one coherent
review-local owner surface. This packet is now the historical predecessor
that resolved the tracked `4fb...` / `5e65...` source-set contract split for
`region1-example-lolo-tylers-kitchen-66344` and proved that the remaining red
belongs to aligned runtime rebaseline instead. It does not reopen the broader
Tyler's Kitchen package-authority lane, change the ECID historical slot
floor, admit Lolo into the governed roster, or scout new replacement
candidates.

Opening closeout commit:
`013b5d1` (`Open Lolo source-set contract blocker`)

## Latest Local Implementation

- Milestone 2 closeout:
  `e2b6941` (`Reduce Lolo source-set blocker Milestone 2`)
- Milestone 3 closeout:
  `a7b4141` (`Open Lolo aligned runtime rebaseline blocker`)

- Milestone 3 is now resolved locally. The tracked replay context and tracked
  `v1-ea-eval` contract now both bind
  `region1-example-lolo-tylers-kitchen-66344` to
  `source-set-5e65d845ce77e1a0`.
- Fresh `v1-ea-eval` on that aligned owner path now closes green with
  `passed=true`, `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`.
- Fresh review `phase-eval` on the aligned owner path remains red at `15/23`.
  The remaining failing phases are `retrieval`, `rule_claim_binding`,
  `downstream_direct_evaluation`, `source_register_contract`,
  `authority_universe`, `generated_rule_pack`,
  `forest_plan_component_eval`, and `evaluation_coverage`.
- The remaining red is not bounded review-local contract realignment work.
  `retrieval` now reads a `5e65...` direct-eval artifact that is stale
  against the current retrieval eval seed and still fails thresholds;
  `rule_claim_binding` now reads a `5e65...` direct-eval artifact that is
  stale against the current rule-claim eval seed while the review-local rule
  pack already uses the generated applicability rule pack; shared
  `downstream_direct_evaluation` still sees `compliance_review_eval` only on
  `f70...`; `generated_rule_pack_validation.json` still reports `4fb...`;
  `source_register_contract` still falls back to the global `4fb...`
  manifest and older workbook SHA; `authority_universe_snapshot.json` still
  fails `source_set_matches`; and `forest_plan_component_eval_results.json`
  still fails only because the tracked eval contract remains on `4fb...`.
- That evidence resolves this packet's scope. The exact next owner is now
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  which owns the stale aligned-runtime artifact and direct-eval family on the
  chosen `5e65...` path.

## Purpose

Determine whether the tracked Lolo review has one truthful contract-chain
owner that can be brought back into alignment, or whether the split itself
stops at another narrower child owner before any review-readiness or roster
work is justified.

Freshness check rule:
before any runtime proving begins, re-read `docs/CURRENT_ROUTING.md`,
`docs/CURRENT_SYSTEM_STATE.md`, the top of `docs/SESSION_HANDOFF.md`,
`config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
`config/v1_lolo_tylers_kitchen_real_ea_eval.json`, the live
`source_library/reviews/region1-example-lolo-tylers-kitchen-66344/`
`v1_ea_eval_results.json`, `phase_eval_results.json`,
`review_validation.json`, `applicability/applicability_validation.json`,
`applicability/generated_rule_pack_validation.json`,
`forest_plan_context_summary.json`, `compliance_matrix.json`, and
`forest_plan_component_eval_results.json`. If the tracked source-set IDs,
failed phase families, or governed aggregate routing drift, update this
packet and the current-route docs before implementation continues.

## Current Evidence

- `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and the top of
  `docs/SESSION_HANDOFF.md` now route the remaining tracked Lolo blocker
  through
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  with this packet preserved as the exact predecessor that resolved the
  tracked `4fb...` / `5e65...` contract split and with
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
  preserved as the older predecessor that reduced the generic feasibility
  lane into this narrower contract packet.
- The tracked replay context
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
  now declares `source_set_id="source-set-5e65d845ce77e1a0"`.
- The tracked `v1-ea-eval` contract
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json` now also declares
  `source_set_id="source-set-5e65d845ce77e1a0"`.
- The live review result
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`
  now reports `source_set_id="source-set-5e65d845ce77e1a0"`,
  `contract_status="reviewer_ready"`, `passed=true`, and no failing checks.
- The live review phase result
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`
  now reports `source_set_id="source-set-5e65d845ce77e1a0"`,
  `passed=false`, `passed_phase_count=15/23`,
  `missing_direct_eval_phase_count=0`,
  `identity_mismatch_phase_count=2`, and failing phases
  `retrieval`, `rule_claim_binding`, `downstream_direct_evaluation`,
  `source_register_contract`, `authority_universe`,
  `generated_rule_pack`, `forest_plan_component_eval`, and
  `evaluation_coverage`.
- Review-local outputs are now mostly aligned on the chosen owner path. Fresh
  readback shows `review_validation.json`,
  `applicability/applicability_validation.json`,
  `forest_plan_context_summary.json`,
  `authority_reviewer_resolution_report.json`,
  `compliance_matrix.json`, and
  `forest_plan_component_eval_results.json` all report
  `source_set_id="source-set-5e65d845ce77e1a0"`, while
  `applicability/generated_rule_pack_validation.json` still reports
  `source_set_id="source-set-4fb59e9eb43045cb"`.
- `phase-eval` now proves that the residual debt is narrower and more exact
  than the old `4fb...` contract split:
  - `retrieval` reads a `5e65...` direct-eval summary whose contract SHA no
    longer matches `config/retrieval_eval_seed.json`, and the retrieval eval
    itself still fails case and metric thresholds.
  - `rule_claim_binding` reads a `5e65...` direct-eval summary whose contract
    SHA no longer matches `config/rule_claim_link_eval_seed.json`, even though
    the direct-eval cases themselves pass and the review-local generated rule
    pack path is aligned.
  - `downstream_direct_evaluation` still sees `claim_eval` present on
    `5e65...`, but `retrieval_eval` and `rule_claim_eval` are stale there and
    `compliance_review_eval` is still present only on
    `source-set-f70ea11e04ae3d53`.
  - `source_register_contract` now fails on workbook SHA drift,
    `authority_universe` still fails `source_set_matches=false`,
    `generated_rule_pack` still fails because
    `generated_rule_pack_validation.json` remains on `4fb...`, and
    `forest_plan_component_eval` still reports `component_eval_failed`.
- Governed aggregates remain unchanged and still do not admit Lolo as a ready
  replacement. Fresh non-strict `promotion-suite` remains green for current
  promotion, strict expansion remains red only on the ECID historical slot
  under `historical_source_set_split`, and covered reviewer-ready reviews
  remain limited to East Crazies, West Reservoir, and South Plateau.

## Goal

Leave the repository with one exact owner decision for the tracked Lolo
contract chain:

- either one coherent source-set contract path that can be evaluated further
  without weakening governed gates; or
- one still narrower owner packet or stop condition if the split itself cannot
  be truthfully reconciled here.

Completion means all of the following are true:

- current-facing docs no longer present the remaining Lolo blocker as a
  generic replacement-feasibility issue;
- the exact contract-chain owner surfaces are enumerated from tracked config,
  live review-local artifacts, and direct-eval dependencies together;
- no governed roster, slot-floor, or ready-state contract is weakened; and
- the next owner after this packet, or the exact stop condition inside this
  packet, is named explicitly in tracked docs and handoff.

## Non-Goals

- Do not flip the ECID historical slot to `ready`, delete it, or lower the
  governed expansion floor.
- Do not admit the tracked Lolo review into
  `config/v1_real_package_review_coverage_v1.json` or
  `config/promotion_suite_v1.json` while `v1-ea-eval` or `phase-eval` remain
  red.
- Do not reopen the broader Tyler's Kitchen package-authority and
  forest-registry work in
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`.
- Do not manually patch ignored `source_library/` JSON to force contract
  agreement.
- Do not widen this packet into downloader, catalog, or full-canonical source
  rebuild work unless a later milestone proves there is no narrower owner.

## Scope

- tracked review identity for
  `region1-example-lolo-tylers-kitchen-66344`
- tracked config versus live review-local source-set contract-chain ownership
- review-scoped `phase-eval` failure families only as needed to classify the
  split owner
- current-routing and lineage docs for the exact live blocker route

## Out Of Scope

- broader Tyler's Kitchen package intake or forest-specific registry work
- ECID slot semantics, manifest-floor redesign, or current-promotion reroute
- broad full-canonical source-set rebuilds
- unrelated Lolo queue, Pinyon, or forest-profile backlog work

## Owner Surfaces

- live blocker docs:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/AGENT_START_HERE.md`
- preserved predecessor and lineage docs:
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- tracked contract surfaces:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`
- live ignored review outputs:
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/`
- command owners and focused tests if code or contract changes become
  necessary:
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_phase_eval.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_promotion_suite.py`,
  `tests/test_cli_eval.py`

## Placement Rules

- Keep broader Tyler's Kitchen package-authority, queue-boundary, and forest
  registry history in
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`. Do not resume
  live runtime work there while this blocker remains active.
- Keep generic replacement-feasibility routing in the predecessor packet only
  as historical context. All live owner truth for the split now belongs here.
- Keep source-set owner truth declarative in tracked config and live artifact
  readback. Do not hide it in prose alone or in ad hoc runtime branches.
- Keep governed roster and slot-floor contracts unchanged until the tracked
  review is reviewer-ready under one coherent source set.
- Keep ignored review evidence local under `source_library/`; commit only
  tracked docs, configs, code, and tests.

## Weak-Point Prevention Contract

- Weak point forecast: a later session patches whichever contract file last
  made `v1-ea-eval` red and declares the split resolved without checking the
  full owner chain.
  Owner surface:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/`
  Prevention gate: Milestone 1 must read the replay context, the eval
  contract, the live `v1_ea_eval_results.json`, the live
  `phase_eval_results.json`, and the representative review-local artifacts
  together before choosing an owner.
  Fail threshold: any later slice claims one coherent contract owner while the
  tracked config, live review result, or representative review-local artifacts
  still disagree on `source_set_id`.
  Controlled violation: change only one tracked config file while leaving the
  review-local outputs unchanged; contract-chain readback must reject the
  shortcut.
  Future-Codex misuse scenario: an agent chases the loudest failure and edits
  one file at a time; this packet forces end-to-end owner readback first.

- Weak point forecast: a later session ignores the third owner surface and
  forgets that downstream direct eval is currently stale on `f70...`.
  Owner surface:
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`,
  `config/downstream_direct_eval_v1.json`,
  `config/compliance_review_eval_seed.json`
  Prevention gate: Milestone 1 must record the direct-eval lane statuses and
  whether the contract chain is only `4fb...` versus `5e65...` or also
  depends on stale `f70...` shared eval coverage.
  Fail threshold: a later slice claims a clean two-source-set split while
  `downstream_direct_evaluation` still reports stale `compliance_review_eval`
  on `source-set-f70ea11e04ae3d53`.
  Controlled violation: ignore the direct-eval lane summaries and classify the
  packet as review-local-only; the next rerun will fail on the unowned stale
  lane.
  Future-Codex misuse scenario: an agent opens only the review-local JSONs and
  misses that the contract still depends on a cross-review eval lane; this
  packet keeps that dependency explicit.

- Weak point forecast: the governed ECID slot gets "repaired" by admitting
  Lolo into the roster while contract-chain ownership is still split.
  Owner surface:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/promotion_suite_v1.json`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_promotion_suite.py`
  Prevention gate: any later child packet that changes roster or slot surfaces
  must keep non-strict `promotion-suite` green, strict expansion fail-closed
  until the replacement is truly ready, and the governed slot floor unchanged.
  Fail threshold: the tracked Lolo review is admitted while
  `v1-ea-eval` still reports `contract_status="mismatch"` or
  `phase-eval` remains red.
  Controlled violation: add the Lolo review to the governed roster before the
  contract chain is coherent; focused tests and aggregate evals must fail.
  Future-Codex misuse scenario: an agent tries to prove progress by editing
  the roster first; the aggregate gates must stop that shortcut.

## Milestone Sequence

### Milestone 0 - Exact Packet Open And Routing Reset

Outcome label: reduced

Purpose: close the predecessor replacement-feasibility Milestone 1 truthfully
and move live routing into this narrower packet.

Implementation:

1. Create this packet as the narrower source-set contract owner.
2. Update `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`,
   `docs/SESSION_HANDOFF.md`, `docs/POST_V1_PROMOTION_SUITE.md`,
   `docs/AGENT_START_HERE.md`, and the predecessor lineage docs so live work
   starts here instead of in the generic replacement-feasibility packet.
3. Mark
   `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
   as the historical predecessor that reduced Milestone 1 into this exact
   blocker.

Acceptance criteria:

- Current-facing docs point here by exact filename.
- The predecessor replacement-feasibility packet is preserved as historical
  lineage rather than the active owner.
- No governed roster, slot, or runtime contracts change in this opening slice.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md

git diff --check
```

### Milestone 1 - Contract-Chain Classification

Outcome label: reduced

Purpose: determine whether the tracked contract chain has one coherent
source-set owner, or whether the split already stops at another narrower
owner.

Implementation:

1. Re-read the tracked replay context, the tracked `v1-ea-eval` contract, the
   live `v1_ea_eval_results.json`, the live `phase_eval_results.json`, and the
   representative review-local artifact files named in Current Evidence.
2. Classify which owner surfaces bind `4fb...`, which bind `5e65...`, and
   which still depend on stale `f70...` direct-eval coverage.
3. Decide whether there is one bounded contract-alignment path here. If yes,
   record the exact owner chain and continue to Milestone 2. If not, open one
   still narrower child packet or record the exact feasibility stop condition.

Acceptance criteria:

- Milestone 1 exits with one exact owner-chain conclusion, not mixed
  assumptions.
- The tracked docs enumerate the representative `4fb...`, `5e65...`, and any
  `f70...` surfaces explicitly.
- No governed roster or slot changes land during classification.

Latest local outcome:

- `reduced locally`; current evidence supports `source-set-5e65d845ce77e1a0`
  as the bounded review-local owner path because the representative
  review-local artifact family already converges there and
  `applicability_validation.json` reports `generated_rule_pack_ready=true`.
- The remaining `4fb...` surfaces are now classified as stale tracked
  contract and expectation surfaces plus one stale
  `generated_rule_pack_validation.json`, and the remaining `f70...` surface is
  classified as shared downstream direct-eval debt for Milestone 2.

Verification:

```bash
jq '{review_id, source_set_id, package_path, catalog_dir, source_manifest_path}' \
  config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json

jq '{review_id, source_set_id, package_path, required_review_artifact_ids, expected_summary}' \
  config/v1_lolo_tylers_kitchen_real_ea_eval.json

jq '{review_id: .summary.review_id, source_set_id: .summary.source_set_id, passed: .summary.passed, contract_status: .summary.contract_status, failed_checks: [.summary.checks[] | select(.passed == false) | {name, details}]}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json

jq '{review_id, source_set_id, passed, passed_phase_count, phase_count, reviewer_ready, missing_direct_eval_phase_count, threshold_failed_phase_count, failed_phase_names: [.phases[] | select(.passed == false) | .name]}' \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json

for f in \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/review_validation.json \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/forest_plan_context_summary.json \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/authority_reviewer_resolution_report.json \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/compliance_matrix.json \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/forest_plan_component_eval_results.json \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/applicability_validation.json \
  source_library/reviews/region1-example-lolo-tylers-kitchen-66344/applicability/generated_rule_pack_validation.json; do
  printf '%s\n' "$f"
  jq '{review_id: (.review_id // .summary.review_id // null), source_set_id: (.source_set_id // .summary.source_set_id // null), rule_pack_id: (.rule_pack_id // .summary.rule_pack_id // null), passed: (.passed // .summary.passed // null)}' "$f"
done
```

### Milestone 2 - Contract-Aligned Review-Readiness Classification

Outcome label: reduced

Purpose: if Milestone 1 identifies one coherent contract-chain owner, decide
whether the remaining red is bounded review-local work or broader runtime
debt.

Implementation:

1. Rebaseline the tracked review only on the owner chain chosen in Milestone 1.
2. Require explicit owner explanations for the remaining failing
   `phase-eval` families before calling the path supportable.
3. If the remaining work is bounded and review-local, continue to Milestone 3.
   If not, open the exact narrower blocker that owns the remaining debt rather
   than broadening this packet.

Acceptance criteria:

- Milestone 2 exits with one exact classification of the remaining red phases.
- No candidate is treated as reviewer-ready while `phase-eval` remains red.
- The governed slot floor remains unchanged.

Latest local outcome:

- `reduced locally`; the tracked replay context and tracked review eval
  contract now align to `source-set-5e65d845ce77e1a0`, and fresh
  `v1-ea-eval` closes green with `contract_status="reviewer_ready"`.
- The remaining red is not bounded review-local contract realignment work.
  Fresh review `phase-eval` on the aligned owner path remains red at `15/23`
  because the residual debt now spans exact runtime and stale-artifact owner
  families: retrieval direct-eval staleness plus failing thresholds,
  rule-claim direct-eval staleness, shared `f70...` compliance direct-eval
  staleness, stale workbook and authority-universe snapshots, stale
  `generated_rule_pack_validation.json`, and a still-failing
  `forest_plan_component_eval_results.json`.
- Governed aggregates remain unchanged and still do not admit Lolo as a ready
  replacement.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344 \
  --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344

PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```

### Milestone 3 - Exact Child-Route Or Feasibility-Stop Closeout

Outcome label: resolved

Purpose: leave the tracked Lolo contract-chain blocker with one exact next
owner and close the packet truthfully.

Implementation:

1. Update the current docs, handoff, and this plan with the exact child packet
   chosen in Milestone 1 or Milestone 2, or with the exact narrower
   feasibility stop if no bounded path exists.
2. Preserve the predecessor replacement-feasibility packet and the broader
   Tyler's Kitchen packet as historical lineage only.
3. Stage only the verified tracked docs and any child-packet file created in
   this closeout, then create one atomic local commit.

Acceptance criteria:

- Current-facing docs no longer leave the next owner generic.
- The blocker either routes to one named child packet or records one explicit
  feasibility stop condition.
- The handoff records the exact verification bundle.

Latest local outcome:

- `resolved locally`; current readback proves that the remaining red no longer
  belongs to source-set contract alignment.
- The exact next owner is now
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  because the residual `phase-eval` family is one aligned-runtime rebaseline
  lane: stale `5e65...` retrieval and rule-claim direct-eval contracts, stale
  shared `f70...` compliance-review direct eval, stale review-local
  `authority_universe_snapshot.json` and `generated_rule_pack_validation.json`,
  a forest-plan component eval contract still pinned to `4fb...`, and a
  `source_register_contract` phase still anchored to the global `4fb...`
  source-set manifest and workbook SHA.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md

git diff --check
```

## Required Implementation Artifacts

- this blocker plan
- exact current-facing routing to this packet
- preserved predecessor and lineage docs
- one named child packet or one narrower feasibility stop before this packet
  closes

## Required Documentation And Handoff Updates

- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/AGENT_START_HERE.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
- `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- this plan

## Required Verification Gates

- plan lint for any touched milestone plan docs
- `git diff --check`
- Milestone 1 contract-chain readback from tracked config, live review result,
  live phase result, and representative review-local artifacts
- if Milestone 2 executes live proving:
  the tracked replacement review's `v1-ea-eval`, `phase-eval`,
  `real-package-review-coverage-eval`, and non-strict `promotion-suite`
- if any later child packet changes roster, manifest, or runtime surfaces:
  focused `promotion-suite`, coverage, and review-stack tests plus the repo's
  stricter gates for the touched surface

## Acceptance Criteria

- The repository no longer routes future sessions to a generic replacement
  blocker or to the broader Tyler's Kitchen packet as live runtime work.
- The tracked Lolo review's contract-chain split is frozen in tracked docs and
  tied to an exact next owner decision.
- The governed expansion slot floor and fail-closed slot contract remain
  unchanged while routing this blocker.
- The next packet after this blocker, or the exact feasibility stop, is named
  explicitly in tracked docs and handoff.

## Stop Conditions

- Stop if the only apparent way forward is to admit Lolo into the governed
  roster before `phase-eval` and `v1-ea-eval` both close green.
- Stop if the tracked review identity split requires broad downloader,
  catalog, or full-canonical work outside a narrow review-local boundary and
  no smaller owner can be named.
- Stop if the remaining review-red phases depend on broad unrelated runtime
  work and no narrower owner can be named.
- Stop if Milestone 1 proves the owner chain is still not bounded inside this
  packet; in that case, open the still narrower blocker rather than broadening
  this packet.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no milestone in this plan may be marked
  complete, `resolved`, or `reduced` until verification passes, durable
  docs/handoff updates land, and the local atomic commit exists. A verified
  but uncommitted slice is only ready-to-close.
- Stage only the verified tracked slice for this blocker packet.
- Leave unrelated dirty or untracked files alone.
- Keep ignored `source_library/` evidence local.
- Include this blocker plan, the touched routing docs, and any named child
  packet opened during closeout in the same commit.
- Record the exact verification bundle in `docs/SESSION_HANDOFF.md`.
- Preserve anti-test-weakening rules: do not weaken or loosen gates, skip
  checks, or lower the governed slot floor to make replacement routing look
  green.

## Residual Risks And Next Milestone Routing

- This packet is now historical predecessor context only. The tracked source-set contract
  split is resolved locally, but the aligned runtime family remains open.
- The next live work is Milestone 0 in
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`:
  freshness-lock the stale aligned-runtime artifacts and direct-eval
  contracts before any reruns.
- If the aligned runtime family refreshes cleanly and retrieval still remains
  semantically red, the next owner after that child should be a narrower
  retrieval/rule-claim quality packet rather than a return to generic Lolo
  contract or ECID replacement classification.
