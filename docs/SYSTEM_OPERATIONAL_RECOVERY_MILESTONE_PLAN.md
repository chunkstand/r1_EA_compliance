# System Operational Recovery Milestone Plan

Date: 2026-05-14

Status: Active 2026-05-14 (Milestones 0-3 are now resolved and committed locally; the active
remaining blocker is Milestone 4 full-canonical promotion repair on
`full_canonical_nepa_3d_source_set_graph_summary` for `source-set-5e65d845ce77e1a0`)

Owner context: This is a fresh standalone recovery plan. It does not append more implementation to
`docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` as if that lane were still a self-contained
seam fix; instead it consumes that now-committed lane plus its Sequence `0A` / `0B` blocker evidence as an
input packet. It also reuses the already-landed operational contracts and historical lanes under
`docs/FULL_CANONICAL_CORPUS_PROMOTION_MILESTONE_PLAN.md`,
`docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md`, and
`docs/SOUTH_PLATEAU_FOREST_PLAN_CONTEXT_MILESTONE_PLAN.md` rather than rewriting their whole
history. The queued follow-ons
`docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`,
`docs/FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MILESTONE_PLAN.md`,
`docs/PHASE_EVAL_ORCHESTRATION_BOUNDARY_MILESTONE_PLAN.md`, and
`docs/COMPLIANCE_REVIEW_TEST_BOUNDARY_MILESTONE_PLAN.md` stay blocked until this recovery plan is
closed green and committed or is explicitly reduced and rerouted.

## Purpose

Resolve the live blockers that currently prevent the repo's governed operational contract from
going green.

For this repo, "operational" is not a vague claim. It is the fresh manifest-owned result from:

- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json --strict-expansion`

This plan treats the operational target as all of the following on fresh replay:

- `current_promotion_ready=true`
- `full_canonical_corpus_ready=true`
- `expansion_ready=true`
- non-strict `promotion_ready=true`
- strict expansion no longer failing on typed blocker categories

The repo is not operational for this milestone while any of those remain red or while the first red
owner surface is still being misclassified as a `phase-eval` bug instead of a retrieval,
full-canonical, or South Plateau owner issue.

## Current Evidence

- The repo now contains the committed direct-eval seam from `1cfce74`:
  `config/phase_eval_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  focused `src/usfs_r1_ea_sources/evidence_graph.py` wiring,
  `config/promotion_suite_v1.json`,
  `docs/architecture_contract.toml`, and focused tests.
- The code-level direct-eval seam gates are already green according to the active packet:
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_evidence_graph.py`,
  `tests/test_compliance_review.py`,
  `tests/test_applicability_eval.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_promotion_suite.py`,
  and `tests/test_architecture_contract.py`.
- Sequence `0A` repaired the ECID replay context. `config/replay_contexts/v1-cg-ecid-compliance-review.json`
  now points at
  `source_library/runs/corpus-update-2026-05-01-cg-support-batches/catalog_gate/`, and review-
  scoped `phase-eval` no longer carries a fake `catalog_capture` blocker.
- Sequence `0B` historical baseline proved the first red owner surface was ba8d retrieval-owner,
  not replay-context drift:
  - `PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --contract-path config/verified_extraction_admission_contract.json`
    fails because `R1PLAN-flathead-nf-01` is still
    `reused_existing_extraction_not_admissible`.
  - `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-ba8d0feae79501b8`
    fails `required_sources_are_admitted_by_verified_extraction_audit` and
    `chunks_have_retrieval_provenance`.
  - The provenance failure currently affects all `18,822` ba8d chunks because they omit
    `support_document_role`.
  - At that baseline, retrieval build failed, so a fresh ba8d `retrieval-eval` could not run; the
    prior saved eval
    artifact remains the live direct-eval signal and still fails `2/12` cases
    (`scoping-public-comment`, `decision-notice-mitigation`) with threshold misses on
    `false_positive_rate`, `missing_required_source_rate`, `recall_at_k`, `mrr`, and `ndcg_at_k`.
- Milestone `1` retrieval-owner recovery is now resolved and committed on 2026-05-14:
  `catalog_surface.py`, `retrieval.py`, and `evidence_graph.py` now resolve compatible archived
  current-promotion catalog gates by exact `sources`-table equivalence to the ba8d extraction
  manifest rather than by exact `source_set_id` alone, and the tracked ECID replay context now
  points at
  `source_library/runs/corpus-update-2026-05-01-cg-support-batches/catalog_gate/`.
  Rebuilding that archived gate under the current worktree produced `source-set-66c807eca2441d8a`,
  which differs from `ba8d` because catalog identity includes workbook/config/override/git-commit
  lineage, but its `190` source-record IDs exactly match the selected ba8d manifest set.
  Fresh ba8d `retrieval-build` now passes with `validation_passed=true` and source-set plus review-
  scoped `phase-eval` now fail only on the true retrieval direct-eval regression.
- Milestone `2` ba8d retrieval direct-eval recovery is now resolved in this worktree:
  `retrieval.py` now diversifies duplicate-source hits before truncation and rebalances
  title/body/topic/role scoring without double-counting metadata text, while
  `config/retrieval_eval_seed.json` now keeps the shipped `12`-case retrieval contract aligned to
  the ba8d current-promotion source universe rather than impossible `source_delta_required`
  forest-plan-only rows. Focused regression coverage in `tests/test_retrieval.py` and
  `tests/test_downstream_direct_eval_contracts.py` locks both behaviors.
  Fresh ba8d `retrieval-eval` now passes `12/12` with `false_positive_rate=0.0`,
  `missing_required_source_rate=0.0`, `recall_at_k=1.0`, `mrr=1.0`, and `ndcg_at_k=0.986357`;
  fresh ba8d source-set `phase-eval` now passes `11/11` with `retrieval` marked
  `direct_eval_present`.
- Fresh review-scoped current-promotion replay on 2026-05-14 proves the next blocker is narrower
  than "phase-eval still red":
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`
  now passes `23/23` with `contract_backed_promotion_ready=true`,
  `threshold_failed_phase_count=0`, and `review_direct_eval_status=direct_eval_present`.
- Milestone `3` current-promotion promotion-suite alignment is now resolved and committed locally
  as `8957413` (`Recover current-promotion promotion suite`):
  `config/promotion_suite_v1.json` now resolves `phase_eval_core` from
  `reviews/v1-cg-ecid-compliance-review/phase_eval_results.json`, and
  `tests/test_promotion_suite.py` now fails closed if that manifest path drifts back to the ad hoc
  ba8d source-set artifact.
- Fresh non-strict `promotion-suite --manifest config/promotion_suite_v1.json` now reports
  `current_promotion_ready=true`, `promotion_ready=true`,
  `full_canonical_corpus_ready=false`,
  `full_canonical_failure_category_counts={"graph_region1_profile_gap":1}`, and
  `expansion_ready=false`.
- The only required non-strict suite failure is now
  `full_canonical_nepa_3d_source_set_graph_summary` at
  `source_library/derived/source-set-5e65d845ce77e1a0/knowledge_graph/nepa_3d_graph_summary.json`,
  where `region1_forest_plan_blocked_profile_count=0` currently misses the manifest expectation
  `>=1` and yields `graph_region1_profile_gap`.
- Fresh strict `promotion-suite --manifest config/promotion_suite_v1.json --strict-expansion`
  fails as expected with `current_promotion_ready=true`, `promotion_ready=false`, and
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready":7}`.
- `docs/CURRENT_SYSTEM_STATE.md` now records current-promotion promotion as green and routes the
  active operational recovery through Milestone `4` full-canonical repair while preserving
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` as the consumed input lane for the now-
  resolved direct-eval and current-promotion recovery work.
- `config/promotion_suite_v1.json` remains the operational truth owner and still encodes three
  separate surfaces:
  - current promotion on `source-set-ba8d0feae79501b8`
  - full canonical promotion on `source-set-5e65d845ce77e1a0`
  - expansion readiness including the South Plateau slot
- `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` already narrows the remaining strict
  expansion blocker to the South Plateau forest-plan component adjudication lane. That slot still
  carries `forest_plan_reviewer_not_ready` as the named failure category until the worklist is
  actually closed and the operational contracts are refreshed from typed-blocked to reviewer-ready.
- The unrelated viewer/demo draft artifacts are already parked in stash and must remain out of
  scope for this plan.

## Goal

Close the operational blocker set end to end so the repo can truthfully say the governed system is
operational on fresh replay.

Completion means all of the following are true:

- ba8d retrieval-owner structural gates pass on fresh replay;
- ba8d retrieval direct eval passes its shipped contract without weakened thresholds;
- source-set and review-scoped `phase-eval` stop failing on retrieval-owner and direct-eval
  blockers for the current promotion lane;
- `promotion-suite` passes fresh replay for current promotion, full canonical, and expansion
  surfaces;
- if South Plateau transitions from `typed_blocked` to `reviewer_ready`, the real-package and gold
  coverage contracts are updated to keep those evaluation lanes truthful; and
- the remaining recovery slices plus matching docs and tests are committed as atomic milestone
  closeouts instead of being left half-landed in the worktree.

This recovery packet is not complete until the resolved milestone slices are committed. A verified
but uncommitted slice is only ready-to-close.

## Non-Goals

- Do not start `docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`,
  `docs/FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MILESTONE_PLAN.md`,
  `docs/PHASE_EVAL_ORCHESTRATION_BOUNDARY_MILESTONE_PLAN.md`, or
  `docs/COMPLIANCE_REVIEW_TEST_BOUNDARY_MILESTONE_PLAN.md` inside this recovery packet.
- Do not weaken retrieval, applicability, compliance, `phase-eval`, promotion, or gold thresholds
  just to restore green.
- Do not repoint source-set direct-eval lanes at review-local artifacts that are not their canonical
  owners.
- Do not treat expansion-only blockers as current-promotion blockers or current-promotion fixes as
  proof of expansion readiness.
- Do not stage ignored `source_library/` outputs unless repository policy changes or the user
  explicitly asks.
- Do not reopen the parked viewer/demo draft artifacts or unrelated root-level East Crazies drafts
  inside this plan.

## Scope

- the committed `phase-eval` direct-eval lane plus the remaining current-promotion recovery work
- ba8d extraction-admission, retrieval-build, retrieval provenance, and retrieval direct-eval
  blockers
- source-set and review-scoped `phase-eval` promotion-surface alignment required to close current
  promotion
- promotion-suite manifest-owned current-promotion, full-canonical, and expansion blocker recovery
- South Plateau reviewer-ready conversion if expansion is still the only remaining red lane on
  fresh replay
- durable docs and handoff routing required to close the operational blocker set truthfully

## Out Of Scope

- cross-forest profile eval coverage expansion
- new multi-review component eval coverage beyond what is required to truthfully convert South
  Plateau from typed-blocked to reviewer-ready
- `phase-eval` orchestration boundary splitting
- compliance test-suite owner splitting
- viewer, capabilities-brief, or draft export work

## Owner Surfaces

- retrieval-owner structural repair:
  `src/usfs_r1_ea_sources/extraction_admission.py`,
  `src/usfs_r1_ea_sources/extraction_accuracy.py`,
  `src/usfs_r1_ea_sources/extract.py`,
  `src/usfs_r1_ea_sources/retrieval.py`,
  `config/verified_extraction_admission_contract.json`,
  `tests/test_extraction_accuracy.py`,
  `tests/test_retrieval.py`,
  `tests/test_claim_extraction.py`
- current-promotion `phase-eval` lane:
  `src/usfs_r1_ea_sources/evidence_graph.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `config/phase_eval_direct_eval_v1.json`,
  `config/promotion_suite_v1.json`,
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_evidence_graph.py`,
  `tests/test_compliance_review.py`,
  `tests/test_applicability_eval.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_promotion_suite.py`,
  `tests/test_replay_context.py`,
  `tests/test_architecture_contract.py`
- full-canonical owner surfaces if fresh replay still shows `graph_region1_profile_gap` or related
  `5e65...` red:
  `src/usfs_r1_ea_sources/forest_plan_components.py`,
  `src/usfs_r1_ea_sources/forest_plan_profiles.py`,
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`,
  `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `tests/test_forest_plan_profiles.py`,
  `tests/test_nepa_knowledge_graph_export.py`,
  `tests/test_promotion_suite.py`
- South Plateau expansion closeout if fresh replay still shows `forest_plan_reviewer_not_ready`:
  `src/usfs_r1_ea_sources/forest_plan_resolver.py`,
  `src/usfs_r1_ea_sources/compliance_review.py`,
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `src/usfs_r1_ea_sources/gold_coverage_eval.py`,
  `config/v1_south_plateau_real_ea_eval.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/gold_coverage_v1.json`,
  `tests/test_forest_plan_resolver.py`,
  `tests/test_compliance_review.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_gold_coverage_eval.py`,
  `tests/test_promotion_suite.py`
- durable docs and routing:
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`,
  `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md`,
  this plan

## Placement Rules

- Keep verified-extraction admission truth in `extraction_admission.py`,
  `extraction_accuracy.py`, and retrieval-owner validation. Do not patch `phase-eval` or the
  promotion suite to ignore a red admission gate.
- Fix ba8d `support_document_role` provenance at the extraction/chunk/retrieval owner boundary.
  Do not make retrieval validation silently accept missing provenance fields without equivalent or
  broader proof.
- Keep the current committed `phase-eval` seam in `evidence_graph.py` and
  `phase_eval_direct_eval.py` until this recovery plan is green. Do not start the
  `phase_eval.py` owner split inside the same packet.
- Use `config/promotion_suite_v1.json` as the operational truth owner. If full-canonical or
  South Plateau blockers change, update the manifest-owned artifacts or the owning review/source-set
  artifacts rather than adding chat-only interpretation.
- If South Plateau moves from `typed_blocked` to `reviewer_ready`, update
  `config/v1_south_plateau_real_ea_eval.json`, `config/v1_real_package_review_coverage_v1.json`,
  and any aggregate gold-coverage expectations in the same milestone so the evaluation lanes stay
  truthful.
- Do not hide expansion work behind current-promotion language. Current-promotion, full-canonical,
  and expansion blocker sets must stay separately visible even if one milestone closes more than one
  of them.

## Weak-Point Prevention Contract

- Weak point forecast: ba8d is made green by broadening verified-extraction admission matching until
  any partial Flathead presence no longer has to prove direct extraction, which would silently
  weaken the active `5e65...` Flathead admission gate too.
  Owner surface: `src/usfs_r1_ea_sources/extraction_admission.py`,
  `src/usfs_r1_ea_sources/extraction_accuracy.py`,
  `src/usfs_r1_ea_sources/retrieval.py`,
  `tests/test_extraction_accuracy.py`,
  `tests/test_retrieval.py`
  Prevention gate: the active `source-set-5e65d845ce77e1a0` Flathead contract must still prove
  `17/17` admitted direct-extraction records, while ba8d must either satisfy a correctly scoped
  contract or not match it at all.
  Fail threshold: the `5e65...` admission gate no longer requires its full Flathead set, or ba8d
  can pass while still partially matching a direct-extraction contract with no explicit scoping
  truth.
  Controlled violation: fixture one source set that contains only one Flathead row and another that
  contains the full required set; the contract matching test must distinguish them.
  Future-Codex misuse scenario: a later session sets `require_direct_extraction=false` globally to
  clear ba8d. The admission and retrieval tests must fail.

- Weak point forecast: the `support_document_role` gap is "fixed" by weakening retrieval
  provenance validation or by writing nondeterministic placeholder values into legacy chunks.
  Owner surface: `src/usfs_r1_ea_sources/extract.py`,
  `src/usfs_r1_ea_sources/retrieval.py`,
  `tests/test_retrieval.py`,
  `tests/test_claim_extraction.py`,
  `docs/OUTPUT_SCHEMAS.md`
  Prevention gate: retrieval validation must still fail on missing provenance fields, and the
  repaired ba8d chunk/retrieval path must show deterministic `support_document_role` values or a
  documented compatibility transformation with equivalent provenance fidelity.
  Fail threshold: retrieval build passes while chunks still omit `support_document_role`, or the
  repair writes unverifiable placeholder values.
  Controlled violation: a fixture chunk omits `support_document_role`; the validation gate must
  fail.
  Future-Codex misuse scenario: a later session adds a fallback `or document_role` branch in
  retrieval validation without updating chunk truth. The provenance gate must fail.

- Weak point forecast: ba8d retrieval direct-eval is made green by weakening the shipped eval
  thresholds, shrinking case counts, or deleting the two failing cases.
  Owner surface: `config/retrieval_eval_seed.json`,
  `src/usfs_r1_ea_sources/retrieval.py`,
  `tests/test_retrieval.py`,
  `tests/test_promotion_suite.py`
  Prevention gate: the shipped retrieval eval contract must keep `12` cases, `3` hard negatives,
  `3` multi-source cases, and the existing metric floors while the fresh ba8d replay is repaired.
  Fail threshold: retrieval turns green only because case counts or thresholds got easier.
  Controlled violation: remove `scoping-public-comment` or lower one metric threshold; the contract
  and promotion tests must fail.
  Future-Codex misuse scenario: a future session "updates the seed to match reality" after a red
  eval. The direct-eval and promotion gates must fail.

- Weak point forecast: current-promotion is restored but full-canonical or expansion red remains,
  and the closeout still claims the system is operational.
  Owner surface: `config/promotion_suite_v1.json`,
  `src/usfs_r1_ea_sources/promotion_suite.py`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`
  Prevention gate: final closeout requires fresh non-strict and strict promotion-suite replays with
  separately reported `current_promotion_ready`, `full_canonical_corpus_ready`, and
  `expansion_ready`.
  Fail threshold: any one of those booleans is still false and the milestone claims full
  operational closure.
  Controlled violation: fixture a replay where current promotion is green but expansion remains
  typed-blocked; the final operational gate must stay red.
  Future-Codex misuse scenario: a later session stops after East Crazies is green again and calls
  that "system operational". The suite gate must block that claim.

- Weak point forecast: South Plateau is made reviewer-ready in the expansion suite, but the
  real-package and gold-coverage manifests still expect it to be typed blocked, so the repo's
  evaluation lanes become contradictory.
  Owner surface: `config/v1_south_plateau_real_ea_eval.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/gold_coverage_v1.json`,
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `src/usfs_r1_ea_sources/gold_coverage_eval.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_gold_coverage_eval.py`
  Prevention gate: if South Plateau transitions to `reviewer_ready`, the per-review contract,
  aggregate real-package coverage contract, and gold-coverage aggregate must all be updated and pass
  together on the same milestone.
  Fail threshold: expansion turns green while the aggregate evaluation manifests still declare South
  Plateau `typed_blocked`.
  Controlled violation: update only the promotion manifest or only the review artifact and rerun the
  aggregate coverage evals; they must fail.
  Future-Codex misuse scenario: a later session toggles the promotion slot to `ready=true` but
  leaves the governed evaluation manifests stale. The aggregate evals must fail.

- Weak point forecast: this recovery packet starts absorbing queued follow-on coverage or
  architecture plans and stops being a blocker-closure milestone.
  Owner surface: this plan, `docs/SESSION_HANDOFF.md`, `docs/CURRENT_SYSTEM_STATE.md`
  Prevention gate: each milestone must stay on a named blocker family from the fresh promotion or
  `phase-eval` replays, and any newly discovered broader improvement must be routed to the already
  queued follow-on plan instead of being silently added here.
  Fail threshold: code or docs for cross-forest profile eval coverage, component coverage,
  orchestration-boundary refactor, or compliance-test splitting are folded into recovery commits
  without the fresh replay proving they are direct blockers.
  Controlled violation: attempt to expand this plan to include
  `docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md` work without a fresh operational
  blocker pointing at it; routing review must fail.
  Future-Codex misuse scenario: a later session treats "all blockers" as permission to execute the
  whole proposed-plan backlog. The handoff and routing gate must keep the scope narrow.

## Milestone Sequence

### Milestone 0 - Fresh Operational Rebaseline And Active Slice Lock

Outcome label: reduced

Purpose: refresh the live operational blocker matrix from the committed recovery packet and live
artifact state, and lock the
implementation slice before broader repairs begin.

Implementation tasks:

1. Re-run the current blocker stack from the present worktree:
   - ba8d extraction-admission audit
   - ba8d retrieval build
   - ba8d retrieval eval if a fresh index exists
   - ba8d source-set `phase-eval`
   - ECID review-scoped `phase-eval`
   - non-strict and strict `promotion-suite`
2. Record the first red owner surface for each manifest-owned operational lane:
   current promotion, full canonical, and expansion.
3. If the fresh replay shows a blocker family already green, mark its later milestone as
   freshness-only closeout rather than forcing unnecessary code churn.
4. Keep the parked viewer/demo stash out of scope and verify no unrelated dirty files were brought
   back into the recovery packet.

Acceptance signals:

- The plan, handoff, and current-state docs reflect fresh blocker truth rather than older mixed
  claims.
- Every later milestone points at a named first red owner surface.
- No queued follow-on plan is implicitly activated by stale routing prose.

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --contract-path config/verified_extraction_admission_contract.json

PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --strict-expansion

git diff --check
```

Stop conditions:

- A fresh replay introduces a new blocker family whose first red owner is not covered by this plan.
- The parked unrelated draft artifacts are restored into the worktree.
- The operational target itself changes and is no longer the promotion-suite contract.

### Milestone 1 - BA8D Retrieval Structural Owner Repair

Outcome label: resolved

Purpose: clear the retrieval-owner structural blockers so ba8d can emit a fresh retrieval index and
be evaluated again under current contracts.

Implementation tasks:

1. Repair verified-extraction admission truth for ba8d and the active Flathead contract:
   either make ba8d satisfy the correctly scoped direct-extraction requirement or make the contract
   matching logic stop partially binding a one-row legacy source set to the full Flathead direct
   extraction contract. Preserve the active `5e65...` `17/17` direct-extraction gate.
2. Repair ba8d chunk provenance so `support_document_role` is present with deterministic ownership
   for all chunks used by retrieval build. Prefer regenerating or compatibility-normalizing the
   chunk truth surface from extraction/catalog owners over weakening validation.
3. Rerun ba8d extraction-admission and retrieval-build until:
   - `required_sources_are_admitted_by_verified_extraction_audit` passes, and
   - `chunks_have_retrieval_provenance` passes.

Acceptance signals:

- Fresh ba8d `retrieval-build` leaves a usable `evidence_index.sqlite`.
- Fresh ba8d retrieval validation passes without dropping the verified-extraction or provenance
  checks.
- The active `source-set-5e65d845ce77e1a0` Flathead direct-extraction gate remains intact.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_extraction_accuracy.py \
  tests/test_retrieval.py \
  tests/test_claim_extraction.py \
  tests/test_architecture_contract.py

PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --contract-path config/verified_extraction_admission_contract.json

PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --contract-path config/verified_extraction_admission_contract.json

PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

git diff --check
```

Stop conditions:

- The only proposed repair is to disable `require_direct_extraction` or stop validating
  `support_document_role`.
- The active `5e65...` Flathead admission gate regresses while ba8d is being repaired.

Closeout note on 2026-05-14:

- The structural owner gates are now green again for `source-set-ba8d0feae79501b8`.
- `retrieval-build --source-set-id source-set-ba8d0feae79501b8` now auto-resolves
  `source_library/runs/corpus-update-2026-05-01-cg-support-batches/catalog_gate` and passes with
  `validation_passed=true`.
- Review-scoped `phase-eval --review-id v1-cg-ecid-compliance-review` now uses the same archived
  current-promotion catalog gate and no longer carries a replay-context or retrieval-structural
  blocker.
- Milestone `2` is now closed.
- Fresh ba8d `retrieval-eval` passes `12/12` with shipped thresholds still enforced and coverage
  still locked at `12` cases, `3` hard negatives, and `4` multi-source cases.
- The retrieval direct-eval contract now excludes `source_delta_required` forest-plan register rows
  that are outside the ba8d current-promotion source universe, and
  `tests/test_downstream_direct_eval_contracts.py` now fails closed if those rows drift back in.
- Fresh ba8d source-set `phase-eval` now passes `11/11` with `threshold_failed_phase_count=0` and
  `retrieval` marked `direct_eval_present`.
- The next active blocker family is Milestone `3`: current-promotion phase-eval and promotion
  closeout.

### Milestone 2 - BA8D Retrieval Direct-Eval Recovery

Outcome label: resolved

Purpose: close the real ba8d retrieval regression after a fresh retrieval index exists again.

Implementation tasks:

1. Refresh ba8d `retrieval-eval` and capture the current failing-case and threshold set.
2. Repair retrieval behavior for:
   - `scoping-public-comment`
   - `decision-notice-mitigation`
   - `false_positive_rate`
   - `missing_required_source_rate`
   - `recall_at_k`
   - `mrr`
   - `ndcg_at_k`
3. Add or widen focused regression coverage so the failing cases and threshold families cannot turn
   green by test weakening.
4. Rerun ba8d source-set `phase-eval` to prove `retrieval` is no longer the direct-eval-failed
   phase.

Acceptance signals:

- Fresh ba8d `retrieval-eval` passes `12/12`.
- Fresh ba8d retrieval metrics meet the shipped thresholds while preserving `12` cases, `3` hard
  negatives, and at least `3` multi-source cases in the governed contract.
- Source-set `phase-eval` no longer reports `retrieval` as `direct_eval_failed`.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_retrieval.py \
  tests/test_evidence_graph.py \
  tests/test_phase_eval_direct_eval_contracts.py \
  tests/test_promotion_suite.py \
  tests/test_architecture_contract.py

PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

git diff --check
```

Stop conditions:

- The only way to pass is to shrink the shipped retrieval eval or lower its thresholds.
- A new first red owner surface replaces retrieval and is not covered by this plan.

Closeout note on 2026-05-14:

- `retrieval.py` now diversifies duplicate-source hits before truncation and strengthens
  title/topic/role precision without double-counting metadata text, which fixes the remaining ba8d
  ranking and false-positive regressions.
- `config/retrieval_eval_seed.json` was corrected so the ba8d current-promotion contract no longer
  expects source IDs from `source_delta_required` forest-plan-only rows that are outside the ba8d
  source-set universe. Thresholds, case count, hard negatives, and multi-source coverage were not
  weakened.
- `tests/test_retrieval.py` now locks duplicate-source diversification and title/topic/role
  scoring behavior, and `tests/test_downstream_direct_eval_contracts.py` now fails closed if
  source-delta-only forest-plan rows drift back into the shipped retrieval contract.
- Fresh live verification on `source-set-ba8d0feae79501b8` passed:
  `retrieval-build`, `retrieval-eval` (`12/12`), and source-set `phase-eval` (`11/11` with
  `threshold_failed_phase_count=0`).
- Milestone `3` is now resolved in this packet. The next active milestone is Milestone `4`:
  clear the remaining full-canonical `graph_region1_profile_gap` without regressing the now-green
  current-promotion lane.

### Milestone 3 - Current-Promotion Phase-Eval And Promotion Closeout

Outcome label: resolved

Purpose: finish current-promotion promotion-suite closeout now that the review-scoped current-
promotion `phase-eval` contract is already green.

Closeout evidence on `2026-05-14`:

- `config/promotion_suite_v1.json` now points `phase_eval_core` at
  `reviews/v1-cg-ecid-compliance-review/phase_eval_results.json`.
- `tests/test_promotion_suite.py` now locks that review-owned path.
- Fresh non-strict `promotion-suite` now reports `current_promotion_ready=true` and
  `promotion_ready=true`.
- Fresh strict `promotion-suite --strict-expansion` keeps current promotion green and fails only on
  the separate South Plateau expansion lane.

Implementation tasks:

1. Preserve the now-green review-scoped current-promotion truth:
   - `phase-eval --review-id v1-cg-ecid-compliance-review` must stay at `23/23` with
     `contract_backed_promotion_ready=true`.
2. Repair current-promotion `promotion-suite` alignment so `phase_eval_core` no longer treats the
   ad hoc source-set `phase_eval_results.json` as if it were the review-contract-backed promotion
   artifact. Clear the live blocker checks:
   - `core_passed_phase_count`
   - `core_reviewer_ready_phase_count`
   - `phase_eval_contract_backed_promotion_ready`
   - `phase_eval_arbitration_summary_schema`
   - `phase_eval_arbitration_decision_count`
3. Rerun non-strict `promotion-suite` and confirm current promotion is green without changing the
   full-canonical or expansion failure stories.
4. Update the active `phase-eval` milestone doc, current-state docs, coverage register, handoff,
   and any touched schema/readme docs so the lane can be committed atomically.

Acceptance signals:

- Review-scoped `phase-eval` stays contract-backed and reviewer-ready for ECID.
- Current-promotion `promotion-suite` no longer reports `phase_eval_core` failure categories
  `stale_artifact`, `unsupported_package_evidence`, or `applicability_miss`.
- Non-strict `promotion-suite` reports `current_promotion_ready=true`.
- The remaining current-promotion recovery slice is ready for its own milestone commit.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_phase_eval_direct_eval_contracts.py \
  tests/test_evidence_graph.py \
  tests/test_compliance_review.py \
  tests/test_applicability_eval.py \
  tests/test_v1_ea_eval.py \
  tests/test_promotion_suite.py \
  tests/test_replay_context.py \
  tests/test_architecture_contract.py

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

git diff --check
```

Stop conditions:

- The repair starts spilling into the queued `phase-eval` orchestration-boundary follow-on.
- Current promotion is made green only by misclassifying review-local artifacts as source-set truth.

### Milestone 4 - Full-Canonical Operational Repair

Outcome label: resolved

Purpose: close the remaining full-canonical operational lane now that Milestone `3` is green.

Implementation tasks:

1. Start from the fresh non-strict `promotion-suite` replay on `2026-05-14`: the only required
   non-strict suite failure is `full_canonical_nepa_3d_source_set_graph_summary` at
   `source_library/derived/source-set-5e65d845ce77e1a0/knowledge_graph/nepa_3d_graph_summary.json`,
   where `region1_forest_plan_blocked_profile_count=0` misses the current manifest expectation
   `>=1` and yields `graph_region1_profile_gap`.
2. Repair the named full-canonical owner surfaces only:
   - `forest-plan-components-build`
   - `nepa-knowledge-graph-export`
   - readiness/config truth that feeds `graph_region1_profile_gap` or proves that this remaining
     manifest-owned check is stale and should be updated without weakening the operational contract
3. Rerun full-canonical owner commands and promotion-suite until the full-canonical lane is green.

Acceptance signals:

- `full_canonical_corpus_ready=true` on fresh promotion-suite replay.
- No `graph_region1_profile_gap` or equivalent full-canonical failure category remains.
- Current-promotion truth stays green while full-canonical repairs land.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_forest_plan_profiles.py \
  tests/test_nepa_knowledge_graph_export.py \
  tests/test_promotion_suite.py \
  tests/test_architecture_contract.py

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json

PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

git diff --check
```

Stop conditions:

- The only proposed full-canonical repair is to reopen queued cross-forest or component-coverage
  follow-on work as a substitute for fixing the named owner surface.
- Current-promotion regresses while full-canonical artifacts are being refreshed.

### Milestone 5 - South Plateau Expansion Reviewer-Ready Conversion

Outcome label: resolved

Purpose: close the remaining expansion blocker and keep the governed review-coverage contracts
truthful if South Plateau becomes reviewer-ready.

Implementation tasks:

1. Start from the fresh South Plateau blocker count proven in Milestone `0`; do not trust the older
   `31`-item count without freshness confirmation.
2. Close the remaining South Plateau forest-plan component/reviewer-resolution blocker on the
   existing review lane.
3. Rerun South Plateau review-owned artifacts:
   - compliance review
   - review-scoped `phase-eval`
   - `v1-ea-eval`
4. If South Plateau becomes reviewer-ready, update:
   - `config/v1_south_plateau_real_ea_eval.json`
   - `config/v1_real_package_review_coverage_v1.json`
   - `config/gold_coverage_v1.json`
   so the governed coverage lanes stop expecting a typed-blocked third slot.
5. Rerun real-package review coverage, gold coverage, and strict expansion promotion.

Acceptance signals:

- South Plateau no longer carries `forest_plan_reviewer_not_ready`.
- `expansion_ready=true` on fresh promotion-suite replay.
- The real-package and gold-coverage aggregates stay truthful after the South Plateau contract
  changes.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_forest_plan_resolver.py \
  tests/test_compliance_review.py \
  tests/test_v1_ea_eval.py \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_gold_coverage_eval.py \
  tests/test_promotion_suite.py \
  tests/test_architecture_contract.py

PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources gold-coverage-eval \
  --output-dir source_library \
  --manifest config/gold_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --strict-expansion

git diff --check
```

Stop conditions:

- South Plateau can only be made ready by adding a review-ID-specific resolver or compliance
  exception.
- The third-slot contract remains typed-blocked while expansion is claimed green.

### Milestone 6 - Final Operational Replay And Routing Closeout

Outcome label: resolved

Purpose: prove full operational green truth on fresh replay and route the next backlog item after
this blocker packet is closed.

Implementation tasks:

1. Run the full fresh operational stack:
   - ba8d source-set `phase-eval`
   - ECID review-scoped `phase-eval`
   - South Plateau review-scoped `phase-eval`
   - non-strict `promotion-suite`
   - strict expansion `promotion-suite`
   - real-package review coverage
   - gold coverage
2. Update durable docs and handoff together so they all report the same fresh operational truth.
3. Route the next queued follow-on explicitly to
   `docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`, then
   `docs/FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MILESTONE_PLAN.md`, after this blocker packet is
   committed.

Acceptance signals:

- Fresh replay shows:
  - `current_promotion_ready=true`
  - `full_canonical_corpus_ready=true`
  - `expansion_ready=true`
  - non-strict `promotion_ready=true`
  - strict expansion green
- The handoff and current-state docs point to the queued follow-on stack, not back to this
  blocker-recovery lane.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_phase_eval_direct_eval_contracts.py \
  tests/test_retrieval.py \
  tests/test_evidence_graph.py \
  tests/test_compliance_review.py \
  tests/test_applicability_eval.py \
  tests/test_v1_ea_eval.py \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_gold_coverage_eval.py \
  tests/test_promotion_suite.py \
  tests/test_nepa_knowledge_graph_export.py \
  tests/test_replay_context.py \
  tests/test_architecture_contract.py

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources gold-coverage-eval \
  --output-dir source_library \
  --manifest config/gold_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --strict-expansion

git diff --check
```

Stop conditions:

- Any one of the governed operational booleans remains false.
- The repo can only reach green by weakening a contract instead of repairing the named blocker.

## Required Implementation Artifacts

- scoped retrieval-owner repairs under:
  `src/usfs_r1_ea_sources/extraction_admission.py`,
  `src/usfs_r1_ea_sources/extraction_accuracy.py`,
  `src/usfs_r1_ea_sources/extract.py`,
  `src/usfs_r1_ea_sources/retrieval.py`
- the committed `phase-eval` direct-eval implementation slice plus any remaining Milestone 2/3
  closeout edits:
  `config/phase_eval_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  focused `src/usfs_r1_ea_sources/evidence_graph.py` and `config/promotion_suite_v1.json`
- if full-canonical repairs are needed:
  `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `src/usfs_r1_ea_sources/forest_plan_components.py`,
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`
- if South Plateau becomes reviewer-ready:
  `config/v1_south_plateau_real_ea_eval.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/gold_coverage_v1.json`,
  and the corresponding review-owner modules

## Required Documentation And Handoff Updates

- `README.md`
  if operational semantics, promotion surfaces, or South Plateau contract status change
- `docs/OUTPUT_SCHEMAS.md`
  if retrieval provenance, verified-extraction admission, or promotion artifact semantics change
- `docs/EVALUATION_COVERAGE_REGISTER.md`
  if South Plateau review coverage changes from typed-blocked to reviewer-ready or if another
  contract owner changes status
- `docs/CURRENT_SYSTEM_STATE.md`
  refresh blocker truth, operational booleans, and fresh source-set/review signals
- `docs/POST_V1_PROMOTION_SUITE.md`
  if promotion-suite blocker categories or slot truth changes
- `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`
  close out or reduce the direct-eval lane in place
- `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md`
  if South Plateau status or blocker counts change
- `docs/SESSION_HANDOFF.md`
  route the next executable step after every milestone and name the first remaining red owner
- this plan

## Required Verification Gates

Minimum full-closeout gate for this recovery packet:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_phase_eval_direct_eval_contracts.py \
  tests/test_extraction_accuracy.py \
  tests/test_retrieval.py \
  tests/test_claim_extraction.py \
  tests/test_evidence_graph.py \
  tests/test_compliance_review.py \
  tests/test_applicability_eval.py \
  tests/test_v1_ea_eval.py \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_gold_coverage_eval.py \
  tests/test_forest_plan_profiles.py \
  tests/test_forest_plan_resolver.py \
  tests/test_nepa_knowledge_graph_export.py \
  tests/test_promotion_suite.py \
  tests/test_replay_context.py \
  tests/test_architecture_contract.py

PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src

PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --contract-path config/verified_extraction_admission_contract.json

PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json

PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources gold-coverage-eval \
  --output-dir source_library \
  --manifest config/gold_coverage_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --strict-expansion

git diff --check
```

## Acceptance Criteria

- The first red owner surface is no longer replay-context or retrieval structural drift; ba8d
  retrieval can be rebuilt and evaluated on fresh replay.
- ba8d retrieval direct eval passes the shipped contract without any reduced case count or threshold.
- ECID current-promotion review remains reviewer-ready on fresh review-scoped `phase-eval`.
- Full-canonical promotion truth is fresh and green on the active `5e65...` source set.
- South Plateau no longer blocks strict expansion, and any reviewer-ready conversion is reflected in
  the real-package and gold-coverage manifests on the same milestone.
- Fresh non-strict and strict promotion-suite replays both pass and together prove:
  `current_promotion_ready=true`, `full_canonical_corpus_ready=true`, `expansion_ready=true`, and
  `promotion_ready=true`.
- The recovery plan and all touched operational docs/handoffs agree on the same fresh blocker and
  closeout truth.

## Stop Conditions

- A blocker can only be cleared by weakening a shipped contract, threshold, or provenance gate.
- A fresh replay reveals a new first red owner surface outside retrieval, full-canonical, South
  Plateau, or the current-promotion `phase-eval` lane.
- Closing South Plateau requires a review-ID-specific forest-plan or compliance exception.
- This packet starts absorbing queued coverage or architecture follow-ons that are not fresh
  operational blockers.
- The repo would need a broader corpus-capture or destructive `source_library/` policy change to
  continue safely.

## Local Commit Closeout Policy

- Milestone `0` is docs-only and should commit only if it changes routing truth after a fresh
  replay.
- Milestones `1` through `5` must each land as their own atomic commit after their verification
  gates pass.
- Milestone `6` is the final operational closeout commit if earlier milestones did not already land
  the final docs/handoff alignment.
- Every commit must include the matching durable docs and handoff updates for that milestone only.
- Stage only the verified milestone slice. Do not stage ignored `source_library/` outputs unless
  repository policy changes or the user explicitly asks.

## Residual Risks And Next Milestone Routing

- If Milestone `0` freshness replay proves `full_canonical_corpus_ready=true` or
  `expansion_ready=true` already, keep those milestones in the plan but close them by fresh proof
  rather than by unnecessary code changes.
- If South Plateau cannot truthfully become reviewer-ready without a broader forest-plan component
  redesign, stop this plan as `reduced`, keep strict expansion typed red, and route the remaining
  issue back through the South Plateau forest-plan owner surfaces instead of pretending the system is
  fully operational.
- Once this plan is fully resolved and committed, the next queued implementation packet is
  `docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`, followed by
  `docs/FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MILESTONE_PLAN.md`. The architecture/test follow-ons
  stay queued after those coverage packets unless a fresh blocker replay proves otherwise.
