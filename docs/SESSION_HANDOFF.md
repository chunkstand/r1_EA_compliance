# Session Handoff

Date: 2026-05-14

Note: this handoff is append-only. For the forest-plan inventory lane, the most recent section for
that lane supersedes older sections below when they disagree.

## System Operational Recovery Milestone 5 Closeout

This update supersedes the earlier top recovery notes where they still routed the repo through
South Plateau strict-expansion blocker recovery.

- committed recovery truth:
  Milestone `5` is now implemented in tracked config/tests/docs. South Plateau is governed by
  `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`,
  `config/forest_plan_component_adjudications/region1-expansion-south-plateau-landscape-treatment.json`,
  the reviewer-ready `config/v1_south_plateau_real_ea_eval.json` contract,
  `config/v1_real_package_review_coverage_v1.json`, `config/gold_coverage_v1.json`, and the
  refreshed South Plateau expansion slot in `config/promotion_suite_v1.json`.
- live South Plateau closeout truth:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment --adjudication-file config/forest_plan_component_adjudications/region1-expansion-south-plateau-landscape-treatment.json`
  passed with `resolved_adjudication_count=31`, `pending_adjudication_count=0`, and
  `system_miss_count=31`;
  `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review --package-path source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment --output-dir source_library --rule-pack source_library/reviews/region1-expansion-south-plateau-landscape-treatment/applicability/generated_rule_pack.json --source-set-id source-set-ba8d0feae79501b8 --review-id region1-expansion-south-plateau-landscape-treatment --reuse-package-cache`
  returned `reviewer_ready=true`;
  `v1-ea-eval --review-id region1-expansion-south-plateau-landscape-treatment` passed with
  `contract_status="reviewer_ready"` and `package_style_tags=["reviewer_ready_expansion"]`; and
  South Plateau review-scoped `phase-eval` now passes `19/19` with
  `contract_backed_promotion_ready=true`.
- live ECID expansion replay truth:
  the ad hoc ECID expansion artifact must be replayed on the ba8d source set rather than the
  active `5e65...` source set. The correct closeout command is
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --review-id region1-expansion-ecid-preliminary-ea`,
  which now passes `19/19` with `declared_review_contract=false`,
  `contract_backed_promotion_ready=false`, and no identity-mismatch blockers.
- aggregate coverage truth:
  `real-package-review-coverage-eval --manifest config/v1_real_package_review_coverage_v1.json`
  now passes with `reviewer_ready_slot_count=3` and `typed_blocked_slot_count=0`. The
  `gold_coverage_eval_results.json` artifact is green with `reviewer_ready_review_count=3` and
  `typed_blocked_review_count=0`; the shell command still has an intermittent non-returning
  session behavior, but the artifact stayed green and fresh promotion-suite replays consumed it
  successfully.
- live operational truth:
  fresh non-strict and strict
  `promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json` replays
  now both pass with `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `expansion_ready=true`, `promotion_ready=true`, and `expansion_failure_category_counts={}`.
- routing truth:
  `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md` is now fully resolved. If the queued
  follow-on stack resumes, start with Milestone `0` in
  `docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`.

## System Operational Recovery Milestone 4 Alignment Pass

This update supersedes the earlier top recovery note only on date stamping, not on blocker
ownership or live promotion truth.

- operator-facing date truth:
  Milestone `4` closeout commit `eaf4acc` (`Recover full-canonical promotion suite`) is dated
  `2026-05-14`, so the top recovery plan, `README.md`, and `docs/CURRENT_SYSTEM_STATE.md` now all
  use `2026-05-14` for that closeout instead of the impossible `2026-05-15` future date.
- live routing truth unchanged:
  non-strict `promotion-suite` still reports `current_promotion_ready=true`,
  `full_canonical_corpus_ready=true`, and `promotion_ready=true`, while strict expansion still
  fails only on `expansion_failure_category_counts={"forest_plan_reviewer_not_ready":7}`.
- routing truth:
  Milestones `0-4` remain resolved. The active next step is still Milestone `5`: South Plateau
  strict expansion reviewer-ready conversion.

## System Operational Recovery Milestone 4 Closeout

This update supersedes the earlier top recovery note where it still said the active blocker was the
full-canonical graph/profile lane.

- committed full-canonical routing truth:
  `config/promotion_suite_v1.json` now requires the real active-source-set graph completeness
  signal for `full_canonical_nepa_3d_source_set_graph_summary`
  (`region1_forest_plan_graph_ready_profile_count>=10` and
  `region1_forest_plan_blocked_profile_count=0`) instead of the stale expectation that some
  promoted Region 1 profiles must remain blocked.
- live full-canonical replay truth:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  passed with `1416` components, `397` standards, and `component_source_accuracy_passed=true`;
  `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`
  passed with `66` checks, `0` failed, `region1_forest_plan_graph_ready_profile_count=10`, and
  `region1_forest_plan_blocked_profile_count=0`.
- live promotion truth:
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
  now passes with `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `promotion_ready=true`, `full_canonical_failure_category_counts={}`, and `expansion_ready=false`.
- live remaining blocker truth:
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json --strict-expansion`
  still fails as expected with `current_promotion_ready=true`, `promotion_ready=false`, and
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready":7}`.
- routing truth:
  Milestones `0-4` in `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md` are now resolved. The
  active next step is Milestone `5`: South Plateau strict expansion reviewer-ready conversion.

## System Operational Recovery Milestone 3 Closeout

This update supersedes the earlier top recovery notes where they still said current promotion was
blocked inside `promotion-suite`.

- committed current-promotion routing truth:
  Milestone `3` is committed locally as `8957413` (`Recover current-promotion promotion suite`).
  `config/promotion_suite_v1.json` now resolves `phase_eval_core` from
  `reviews/v1-cg-ecid-compliance-review/phase_eval_results.json` instead of the ad hoc ba8d
  source-set artifact, and `tests/test_promotion_suite.py` now fails closed if that manifest path
  drifts.
- live current-promotion replay truth:
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`
  stays green at `23/23` with `contract_backed_promotion_ready=true`;
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
  now passes with `current_promotion_ready=true`, `promotion_ready=true`,
  `full_canonical_corpus_ready=false`, `full_canonical_failure_category_counts={"graph_region1_profile_gap":1}`,
  and `expansion_ready=false`.
- live remaining blocker truth:
  the only required non-strict suite failure is now
  `full_canonical_nepa_3d_source_set_graph_summary` at
  `source_library/derived/source-set-5e65d845ce77e1a0/knowledge_graph/nepa_3d_graph_summary.json`,
  where `region1_forest_plan_blocked_profile_count=0` misses the current promotion-suite
  expectation `>=1` and yields `graph_region1_profile_gap`.
- strict-expansion truth:
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json --strict-expansion`
  fails as expected with `current_promotion_ready=true`, `promotion_ready=false`, and
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready":7}`.
- output-path truth:
  default `promotion-suite` writes both non-strict and strict-expansion replays under
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/` because the output
  directory keys off manifest id, not the `--strict-expansion` flag. The older
  `.../post-v1-region1-ea-promotion-suite-strict-expansion/` folder is historical only unless a
  future replay passes `--results-dir` explicitly.
- routing truth:
  Milestones `0-3` in `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md` are now resolved. The
  active next step is Milestone `4`: full-canonical NEPA 3D graph/profile alignment on the active
  `5e65...` source set, followed later by Milestone `5` South Plateau strict expansion.

## System Operational Recovery Milestone 2 Alignment Pass

This alignment update supersedes the earlier top recovery note where it still said Milestone `3`
begins by rerunning review-scoped `phase-eval`.

- live current-promotion review truth:
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`
  now passes `23/23` with `contract_backed_promotion_ready=true`,
  `threshold_failed_phase_count=0`, and `review_direct_eval_status=direct_eval_present`.
- live current-promotion blocker truth:
  non-strict and strict `promotion-suite` still report `current_promotion_ready=false`, but the red
  is now narrower than "phase-eval still failing." The failing suite surface is
  `phase_eval_core` at
  `source_library/derived/source-set-ba8d0feae79501b8/evidence_graph/phase_eval_results.json`,
  where promotion still expects review-contract-backed fields from the ad hoc source-set artifact:
  `core_passed_phase_count=11<19`, `core_reviewer_ready_phase_count=11<19`,
  `phase_eval_contract_backed_promotion_ready=false`,
  `phase_eval_arbitration_summary_schema=null`, and
  `phase_eval_arbitration_decision_count=null`.
- routing truth:
  the active next step is still Milestone `3` in
  `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md`, but its real implementation target is now
  current-promotion promotion-suite alignment against the correct phase-eval truth surface, not
  another review-scoped `phase-eval` replay.
- broader operational truth:
  non-strict `promotion-suite` currently fails with
  `failure_category_counts={"applicability_miss":1,"stale_artifact":1,"unsupported_package_evidence":1}`,
  `full_canonical_corpus_ready=false` with `graph_region1_profile_gap`, and
  `expansion_ready=false` with South Plateau `forest_plan_reviewer_not_ready`.
- verification in this alignment pass:
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review` passed `23/23`;
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json` failed with the `phase_eval_core` blocker set above; and
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json --strict-expansion` failed with the same current-promotion blocker set plus the known South Plateau expansion blockers.

## System Operational Recovery Milestone 2 Closeout

This update supersedes the earlier recovery-routing sections below where they still say the live
ba8d blocker is retrieval direct eval.

- committed routing truth:
  the next milestone in `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md` is now Milestone `3`,
  not Milestone `2`. Milestones `0-2` are resolved in the current worktree and are being closed in
  the same atomic milestone commit.
- implemented retrieval recovery:
  `src/usfs_r1_ea_sources/retrieval.py` now diversifies duplicate-source hits before truncation and
  rebalances title/topic/role/body precision without double-counting metadata text.
  `config/retrieval_eval_seed.json` now keeps the shipped ba8d retrieval contract aligned to the
  current-promotion source universe instead of impossible `source_delta_required` forest-plan-only
  rows, and `tests/test_downstream_direct_eval_contracts.py` now fails closed if those rows drift
  back into the contract. `tests/test_retrieval.py` now locks both the diversification and
  precision-scoring behavior.
- live replay after the repair:
  `retrieval-build --source-set-id source-set-ba8d0feae79501b8` passed on the compatible archived
  current-promotion catalog gate;
  `retrieval-eval --source-set-id source-set-ba8d0feae79501b8` passed `12/12` with
  `false_positive_rate=0.0`, `missing_required_source_rate=0.0`, `recall_at_k=1.0`, `mrr=1.0`,
  and `ndcg_at_k=0.986357`;
  source-set `phase-eval --source-set-id source-set-ba8d0feae79501b8` passed `11/11` with
  `threshold_failed_phase_count=0` and `retrieval` marked `direct_eval_present`.
- remaining blocker:
  the active next step is Milestone `3`: rerun review-scoped
  `phase-eval --review-id v1-cg-ecid-compliance-review`, refresh non-strict `promotion-suite`, and
  close the remaining current-promotion docs/routing packet.
- verification in this step:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py tests/test_downstream_direct_eval_contracts.py tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_promotion_suite.py tests/test_architecture_contract.py -q` passed `63/63`;
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/retrieval.py tests/test_retrieval.py tests/test_downstream_direct_eval_contracts.py tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_promotion_suite.py tests/test_architecture_contract.py` passed;
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-ba8d0feae79501b8` passed;
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8` passed `12/12`; and
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8` passed `11/11`.

## System Operational Recovery Alignment Closeout

This alignment update supersedes the earlier recovery-routing sections below where they still talk
about a dirty worktree lane, `catalog_dir=source_library/catalog`, or Milestone `0` as the next
step.

- committed routing truth:
  the recovery packet is already committed as `1cfce74` (`Recover ba8d replay catalog routing`).
  Milestone `0` and Milestone `1` are resolved and committed; the active next step is Milestone
  `2` in `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md`.
- current replay-context truth:
  `config/replay_contexts/v1-cg-ecid-compliance-review.json` now points at
  `source_library/runs/corpus-update-2026-05-01-cg-support-batches/catalog_gate`, not
  `source_library/catalog`. Older handoff entries that still name `source_library/catalog` are now
  historical only.
- active blocker truth:
  ba8d retrieval structural repair is closed. Fresh source-set and review-scoped replays now fail
  only on the real ba8d retrieval direct-eval regression:
  `scoping-public-comment` and `decision-notice-mitigation`, plus threshold misses on
  `false_positive_rate`, `missing_required_source_rate`, `recall_at_k`, `mrr`, and `ndcg_at_k`.
- plan alignment:
  `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md`,
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, and this handoff now route the same next step: Milestone `2`
  retrieval direct-eval recovery, not another replay-context or retrieval-structural pass.
- verification in this alignment pass:
  `git diff --check` passed after the doc updates; no behavioral code changed in this pass.

## System Operational Recovery Milestone 1 Closeout

This update closes the retrieval-owner structural recovery slice and activates Milestone `2` in
`docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md`.

- compatibility catalog truth:
  there is no archived `source_set_manifest.json` in `source_library/runs/` with
  `source_set_id=source-set-ba8d0feae79501b8`. Rebuilding the documented current-promotion base
  batch as a catalog gate under
  `source_library/runs/corpus-update-2026-05-01-cg-support-batches/catalog_gate/` produced
  `source-set-66c807eca2441d8a`, not `ba8d`. That is expected because catalog `source_set_id`
  includes workbook/config/overrides/git-commit lineage, not only selected source rows.
- implemented owner repair:
  `src/usfs_r1_ea_sources/catalog_surface.py` now resolves compatible archived catalog gates by
  exact `sources`-table equivalence to the derived lane's selected extraction-manifest
  source-record set, and `src/usfs_r1_ea_sources/retrieval.py` now accepts a rebuilt catalog when
  that exact row-set proof holds while still failing closed on incompatible catalog universes.
  `src/usfs_r1_ea_sources/evidence_graph.py` uses the same resolver for source-set `evidence-graph`
  and `phase-eval` replays, `config/replay_contexts/v1-cg-ecid-compliance-review.json` now points
  at the archived current-promotion catalog gate, and focused retrieval/evidence-graph/replay-
  context tests cover both the compatible and incompatible paths.
- live replay after the repair:
  `retrieval-build --source-set-id source-set-ba8d0feae79501b8` now auto-resolves
  `source_library/runs/corpus-update-2026-05-01-cg-support-batches/catalog_gate`,
  records `catalog_source_set_id=source-set-66c807eca2441d8a`, and passes with a fresh
  `evidence_index.sqlite`. Source-set and review-scoped `phase-eval` now land on the same catalog
  surface and fail only on the ba8d retrieval direct-eval regression rather than on catalog drift,
  verified-extraction gating, or missing provenance.
- remaining blocker:
  fresh `retrieval-eval --source-set-id source-set-ba8d0feae79501b8` still fails `2/12` cases
  (`scoping-public-comment`, `decision-notice-mitigation`) with threshold misses on
  `false_positive_rate`, `missing_required_source_rate`, `recall_at_k`, `mrr`, and `ndcg_at_k`.
  This is now the true active blocker for Milestone `2`.
- verification in this step:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py tests/test_evidence_graph.py tests/test_extraction_accuracy.py tests/test_replay_context.py tests/test_architecture_contract.py -q` passed `41/41`;
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/catalog_surface.py src/usfs_r1_ea_sources/retrieval.py src/usfs_r1_ea_sources/evidence_graph.py tests/test_retrieval.py tests/test_evidence_graph.py tests/test_replay_context.py` passed;
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-ba8d0feae79501b8` passed with `validation_passed=true` and `catalog_dir=source_library/runs/corpus-update-2026-05-01-cg-support-batches/catalog_gate`;
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8` failed `2/12`;
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8` failed only on retrieval direct-eval thresholds; and
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review` now resolves the archived current-promotion catalog gate and fails only on the same retrieval direct-eval thresholds.
- next step:
  execute Milestone `2` in `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md`: repair ba8d
  retrieval ranking/coverage for `scoping-public-comment` and `decision-notice-mitigation`
  without weakening the shipped eval contract.

## System Operational Recovery Plan Added

The repo now has a fresh standalone recovery packet at
`docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md`.

- routing truth:
  this new plan consumes the current dirty `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`
  slice plus the fresh Sequence `0A` / `0B` blocker classification instead of treating the remaining
  work as phase-eval-only
- operational contract:
  the plan defines "system operational" as fresh non-strict plus strict `promotion-suite` green
  replays with `current_promotion_ready=true`, `full_canonical_corpus_ready=true`, and
  `expansion_ready=true`
- blocker stack captured:
  Milestone `0` replays the live blocker matrix, Milestone `1` repairs ba8d retrieval-owner
  structural blockers, Milestone `2` closes the ba8d retrieval direct-eval regression, Milestone
  `3` closes the dirty current-promotion `phase-eval` lane, Milestone `4` clears any remaining
  full-canonical blockers, and Milestone `5` resolves South Plateau expansion plus any needed
  real-package/gold-contract updates before final operational closeout
- queued follow-ons preserved:
  `docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`,
  `docs/FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MILESTONE_PLAN.md`,
  `docs/PHASE_EVAL_ORCHESTRATION_BOUNDARY_MILESTONE_PLAN.md`, and
  `docs/COMPLIANCE_REVIEW_TEST_BOUNDARY_MILESTONE_PLAN.md` remain out of scope unless a fresh
  replay proves one of them is a direct operational blocker
- next step:
  execute Milestone `0` in `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md` and refresh the
  fresh blocker matrix before any new code changes begin

## Phase-Eval Direct-Eval Sequence 0A Replay-Context Repair

This update resolves the stale ECID replay-context catalog ownership so the active phase-eval lane
can resume from Sequence 0B without carrying a fake `catalog_capture` red.

- repaired replay context:
  `config/replay_contexts/v1-cg-ecid-compliance-review.json` now points `catalog_dir` at
  `source_library/catalog`, which is the canonical catalog surface and contains both
  `catalog_validation.json` and `review_sources.sqlite`
- focused regression guard:
  `tests/test_replay_context.py` now locks the tracked ECID replay context to the canonical catalog
  surface so future sessions cannot silently repoint it at a derived source-set folder
- remaining live blocker after this repair:
  the active lane is still red on the ba8d retrieval owner path, not on replay-context drift;
  `retrieval-build` still fails the separate verified-extraction prerequisite and
  `retrieval-eval` remains the live `2/12` direct-eval failure
- verification in this step:
  `test -f "$(jq -r '.catalog_dir' config/replay_contexts/v1-cg-ecid-compliance-review.json)/catalog_validation.json"` and
  `test -f "$(jq -r '.catalog_dir' config/replay_contexts/v1-cg-ecid-compliance-review.json)/review_sources.sqlite"` now pass;
  `PYTHONPATH=src uv run --extra dev pytest tests/test_replay_context.py tests/test_compliance_review.py tests/test_evidence_graph.py tests/test_architecture_contract.py -q` passed `89/89` with `3` subtests; and
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`
  now resolves `catalog_dir` to `source_library/catalog` and fails only on the real retrieval and
  evaluation-coverage direct-eval blockers
- next step:
  execute Sequence 0B in `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` to determine
  whether the remaining ba8d retrieval red is a prerequisite-owner repair or a true retrieval
  direct-eval regression

## Phase-Eval Direct-Eval Sequence 0B Structural Rebaseline

This update finishes the active milestone's Sequence `0B` classification work. The remaining red is
not replay-context drift anymore; it is a retrieval-owner blocker plus a still-red retrieval direct
eval artifact.

- fresh structural owner replay:
  `PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --contract-path config/verified_extraction_admission_contract.json`
  now proves ba8d still blocks `R1PLAN-flathead-nf-01` because its manifest record is
  `reused_existing_extraction_not_admissible`
- fresh retrieval owner replay:
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-ba8d0feae79501b8`
  still fails before a usable index is emitted. The failed retrieval validation checks are
  `required_sources_are_admitted_by_verified_extraction_audit` and
  `chunks_have_retrieval_provenance`; the second failure currently hits all `18,822` ba8d chunks
  because they omit `support_document_role`
- direct-eval classification after the structural replay:
  the stale replay-context red is gone, but fresh
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8`
  cannot run because the failed retrieval build leaves no `evidence_index.sqlite`.
  The existing ba8d retrieval eval artifact remains the live direct-eval red with `2/12` failed
  cases (`scoping-public-comment`, `decision-notice-mitigation`) and threshold misses on
  `false_positive_rate`, `missing_required_source_rate`, `recall_at_k`, `mrr`, and `ndcg_at_k`
- source-set phase-eval replay:
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8`
  still fails on `retrieval`, `downstream_direct_evaluation`, and `evaluation_coverage`; the
  aggregate remains `threshold_failed_phase_count=1`, but the first red owner surface is now
  explicitly recorded as retrieval-owner, not replay-context
- next step:
  do not resume `phase-eval` edits yet. The next safe implementation slice is a dedicated
  retrieval-owner repair covering ba8d verified-extraction admission for `R1PLAN-flathead-nf-01`
  and the legacy-chunk `support_document_role` provenance gap, followed by a fresh ba8d
  `retrieval-build`, `retrieval-eval`, and `phase-eval` replay before this milestone continues

## Compliance Review Test Boundary Plan

This planning-only update adds a fresh standalone hotspot follow-on for the P2 finding that
`tests/test_compliance_review.py` has become the repo's hottest mixed-owner verification surface.

- scope:
  `docs/COMPLIANCE_REVIEW_TEST_BOUNDARY_MILESTONE_PLAN.md`
- routing truth:
  the new plan does not reopen the production compliance owner splits. It starts only after
  overlapping dirty work in `tests/test_compliance_review.py` is committed or explicitly parked,
  and it refreshes the landed `phase-eval` owner path in Sequence 0 before moving tests.
- planned outcome:
  keep `tests/test_compliance_review.py` as a narrow core orchestration suite, move eval, coverage,
  gold-eval, and compliance-derived `phase-eval` cases into dedicated suites, extract the synthetic
  source-library builders into `tests/support`, and add a boundary gate so the catch-all suite
  cannot regrow silently.
- current evidence captured in the plan:
  `tests/test_compliance_review.py` is currently `4937` lines and the fresh architecture probe
  ranks it as the repo's top hotspot (`48` revisions, hotspot score `236976`), while
  `src/usfs_r1_ea_sources/compliance_review.py` is only `424` lines and the other production
  compliance owners are already separated.
- affected dirty state:
  this follow-on overlaps the currently dirty `tests/test_compliance_review.py` file and active
  docs that still point at it, including `docs/SESSION_HANDOFF.md`; do not start implementation
  until the overlap is either committed or explicitly parked and refreshed in Sequence 0.

## Phase Eval Orchestration Boundary Plan

This planning-only update adds a fresh standalone architecture follow-on for the P1 finding that
`evidence_graph.py` currently owns `phase-eval` orchestration in addition to graph build and
validation.

- scope:
  `docs/PHASE_EVAL_ORCHESTRATION_BOUNDARY_MILESTONE_PLAN.md`
- routing truth:
  the new plan stacks after the current dirty
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` lane closes and is committed or is
  explicitly parked and rebased in the plan's Sequence 0. It does not reopen that lane inside the
  same milestone.
- planned outcome:
  move `run_phase_aligned_eval(...)` and its readiness helper tree into a dedicated canonical owner
  (`src/usfs_r1_ea_sources/phase_eval.py`), tighten the architecture contract so the
  `evidence_graph` layer becomes graph-only again, and split `phase-eval` tests away from
  `tests/test_evidence_graph.py`
- current evidence captured in the plan:
  `src/usfs_r1_ea_sources/evidence_graph.py` is currently `3535` lines, the worktree already has a
  dirty `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`, and the architecture probe plus
  architecture review both point to the same collapsed owner boundary
- affected dirty state:
  this follow-on overlaps currently dirty files in `src/usfs_r1_ea_sources/evidence_graph.py`,
  `docs/architecture_contract.toml`, `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`, and
  `docs/SESSION_HANDOFF.md`; do not start implementation until that overlap is either committed or
  explicitly parked and refreshed in Sequence 0

## Real-Package Review Coverage Closeout

This closeout implements the first stacked follow-on after gold coverage and narrows the lane to
its dedicated owner surfaces instead of reopening the earlier gold milestone.

- scope:
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `src/usfs_r1_ea_sources/gold_coverage_eval.py`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/gold_coverage_v1.json`,
  `docs/architecture_contract.toml`,
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/REAL_PACKAGE_REVIEW_COVERAGE_MILESTONE_PLAN.md`,
  focused tests
- contract/routing truth:
  `config/v1_real_package_review_coverage_v1.json` now owns the three governed slots:
  East Crazies current promotion (`current_promotion_reviewer_ready`),
  West Reservoir (`alternate_package_reviewer_ready`), and
  South Plateau (`typed_blocked_expansion`). `v1-ea-eval` now resolves per-review contracts from
  that manifest when `--review-id` is supplied, and fails closed without either a tracked review ID
  or an explicit `--eval-file`
- aggregate coverage truth:
  `real-package-review-coverage-eval` now passes on the live tracked reviews with
  `required_slot_count=3`, `covered_slot_count=3`, `distinct_forest_count=2`,
  `distinct_package_style_count=3`, `reviewer_ready_slot_count=2`,
  `typed_blocked_slot_count=1`, and `missing_package_authority_count=0`. South Plateau remains a
  first-class typed-blocked slot with matched blocker categories
- gold integration:
  `gold-coverage-eval` now reuses the manifest-owned real-package aggregate instead of carrying a
  second embedded review roster. A bounded integration replay against the current gold result
  artifacts plus the fresh `real_package_review_coverage_eval_results.json` stayed green with
  `required_theme_count=7`, `passed_theme_count=7`, `distinct_forest_count=2`,
  `distinct_package_style_count=3`, `reviewer_ready_review_count=2`, and
  `typed_blocked_review_count=1`
- next follow-on:
  the active next evaluation-strengthening boundary is still
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`, which can now depend on the dedicated
  manifest-owned real-package coverage lane instead of the old ECID-only default path
- affected dirty state:
  unrelated local changes already exist in `tests/test_nepa_3d_viewer.py`,
  `viewer/nepa-3d/app.js`, root-level East Crazies draft exports, and
  `docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf`; leave them out of this milestone slice

Verification in this closeout:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_replay_context.py tests/test_real_package_review_coverage_eval.py tests/test_gold_coverage_eval.py tests/test_v1_ea_eval.py tests/test_cli.py tests/test_architecture_contract.py -q`: passed `84/84`
- `PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`: passed with `contract_status=reviewer_ready`
- `PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id west-reservoir-67436`: passed with `contract_status=reviewer_ready`
- `PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment`: passed with `contract_status=typed_blocked` and matched blocker categories
- `PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`: passed with `3/3` covered slots and `0` authority misses
- bounded gold integration replay from current results via `run_gold_coverage_eval(...)`: passed with `required_theme_count=7`, `passed_theme_count=7`, `distinct_forest_count=2`, `distinct_package_style_count=3`, `reviewer_ready_review_count=2`, and `typed_blocked_review_count=1`

## Gold Coverage Expansion Final Closeout Refresh

This refresh closes the last live current-promotion gap that remained after the earlier gold
coverage implementation section below.

- final gap closed:
  non-strict `promotion-suite` now reports `current_promotion_ready=true`,
  `promotion_ready=true`, `full_canonical_corpus_ready=false`, and `expansion_ready=false`. The
  current-promotion stale-artifact blocker is gone; only the separate full-canonical
  `graph_region1_profile_gap` and South Plateau expansion `forest_plan_reviewer_not_ready` signals
  remain red
- compatibility fixes required for closeout:
  `src/usfs_r1_ea_sources/retrieval.py` now tolerates legacy retrieval indexes missing
  `support_document_role`, and `src/usfs_r1_ea_sources/applicability.py` now falls back to
  `source_library/derived/<source_set_id>/diagnostics/extraction_manifest.jsonl` when the merged
  top-level catalog no longer carries the requested legacy `source_set_id`
- focused regression coverage:
  `tests/test_retrieval.py` now proves legacy retrieval-index reads still return results with
  `support_document_role=None`, and `tests/test_applicability.py` now proves authority-universe
  snapshots can rebuild from the archived extraction manifest when the live catalog only contains a
  newer source set
- refreshed verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability.py tests/test_retrieval.py -q`
  passed `20/20`;
  `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py -k compliance_gold_eval -q`
  passed `8/8`;
  `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --eval-file config/compliance_review_eval_seed.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json`
  passed `5/5` with `source_set_id=source-set-ba8d0feae79501b8`;
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
  passed with `current_promotion_ready=true` and `promotion_ready=true`

## Gold Coverage Expansion Closeout

The gold coverage expansion milestone is now implemented across code, tracked contracts, docs, and
promotion/register wiring.

- scope:
  `src/usfs_r1_ea_sources/applicability_eval.py`,
  `src/usfs_r1_ea_sources/compliance_gold_eval.py`,
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/gold_coverage_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `config/applicability_gold_eval_v1.json`,
  `config/compliance_gold_eval_v1.json`,
  `config/gold_coverage_v1.json`,
  `config/v1_ecid_real_ea_eval.json`,
  `config/v1_west_reservoir_real_ea_eval.json`,
  `config/v1_south_plateau_real_ea_eval.json`,
  `config/replay_contexts/v1-cg-ecid-compliance-review.json`,
  `config/promotion_suite_v1.json`,
  `docs/architecture_contract.toml`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  focused tests
- current gold/review truth:
  `applicability-gold-eval` now passes `12/12` adjudicated cases with `source_chunk_count=19`,
  all `19` high-priority family IDs mapped into seven named coverage groups, and
  `promotion_ready=true`; `compliance-gold-eval` now passes `14/14` adjudicated cases with the
  same seven named coverage tags plus `clean_baseline`, `live_external_noisy`, and
  `typed_blocked_expansion`; `gold-coverage-eval` passes with `required_theme_count=7`,
  `passed_theme_count=7`, `distinct_forest_count=2`, `distinct_package_style_count=3`,
  `reviewer_ready_review_count=2`, and `typed_blocked_review_count=1`
- real-review contract coverage:
  `v1-ea-eval` now carries `forest_unit_id`, `package_style_tags`, expected lane states, and
  allowed blocker categories. The shipped review set now covers East Crazies current promotion
  (`reviewer_ready`), West Reservoir (`reviewer_ready`), and South Plateau (`typed_blocked` on
  `forest_plan_reviewer_resolution_open` plus
  `forest_plan_standard_reviewer_resolution_open`)
- promotion/register wiring:
  `docs/EVALUATION_COVERAGE_REGISTER.md` now marks `applicability_gold_eval`,
  `compliance_gold_eval`, `v1_ea_eval`, and `gold_coverage_eval` as `direct_eval_present`.
  `config/promotion_suite_v1.json` now consumes the widened applicability/compliance thresholds and
  the aggregate `gold_coverage_eval` artifact
- current blocker after closeout:
  current-promotion `promotion-suite` is still red, but the milestone-specific gold coverage gates
  are green. The remaining required current-promotion failure is one stale
  `reviews/compliance_review_eval/compliance_review_eval_results.json` artifact whose source set is
  still `source-set-5e65d845ce77e1a0` instead of the current promotion source set
  `source-set-ba8d0feae79501b8`. Expansion and full-canonical blockers remain separate and
  unchanged
- affected dirty state:
  unrelated local changes already exist in `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md`,
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`, `tests/test_nepa_3d_viewer.py`,
  `viewer/nepa-3d/app.js`, root-level East Crazies draft exports, and
  `docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf`; leave them out of the gold-coverage
  milestone slice

Verification in this closeout:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py -q`: passed `12/12`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_gold_coverage_eval.py -q`: passed `3/3`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_v1_ea_eval.py -q`: passed `24/24`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py -k compliance_gold_eval -q`: passed `8/8`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py tests/test_architecture_contract.py tests/test_cli.py -q`: passed `66/66`
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json --eval-file config/applicability_eval_seed.json`: passed `9/9`
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gold-eval --output-dir source_library --gold-file config/applicability_gold_eval_v1.json`: passed `12/12` with `promotion_ready=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json`: passed `14/14` with required coverage and package-style tags present
- `PYTHONPATH=src python -m usfs_r1_ea_sources gold-coverage-eval --output-dir source_library --manifest config/gold_coverage_v1.json`: passed with `required_theme_count=7`, `passed_theme_count=7`, `distinct_forest_count=2`, `distinct_package_style_count=3`, `reviewer_ready_review_count=2`, and `typed_blocked_review_count=1`
- `python - <<'PY' ... run_promotion_suite(...) ... PY`: current-promotion replay still failed closed only on `compliance_review_eval`; separate full-canonical graph and South Plateau expansion blockers remained unchanged

Residual risks:

- replaying `compliance-review-eval` on `source-set-ba8d0feae79501b8` still crashes before it can
  refresh the stale promotion-suite prerequisite because the local retrieval index is missing the
  newer `support_document_role` column (`IndexError: No item with that key`). This is outside the
  gold-coverage contract work and needs its own refresh or compatibility fix
- `promotion-suite` therefore remains red at the current-promotion layer until that stale
  `compliance_review_eval` artifact is refreshed for the current promotion source set
- full-canonical `graph_region1_profile_gap` and South Plateau expansion
  `forest_plan_reviewer_not_ready` signals remain separate blockers and were not reopened in this
  milestone

## Upstream Evaluation Coverage Closeout

The upstream evaluation coverage milestone is now implemented across code, tracked fixtures, docs,
and readiness wiring.

- scope:
  `config/upstream_evaluation_v1.json`, fixture families under `config/fixtures/upstream_eval/` and
  `tests/fixtures/upstream_eval/`, `src/usfs_r1_ea_sources/upstream_evaluation.py`, CLI
  registration, `phase-eval` wiring, and `docs/EVALUATION_COVERAGE_REGISTER.md`
- current direct-eval truth:
  `upstream-eval` now requires `11` named category families and `22` total cases across capture,
  catalog, and extraction; the current closeout replay passed `22/22` matched cases with
  `failed_case_ids=[]`, and the promoted output family is
  `source_library/evaluations/upstream/upstream_evaluation_results.json` plus
  `source_library/evaluations/upstream/upstream_evaluation_report.md`
- readiness integration:
  source-set and review `phase-eval` now surface a separate `upstream_evaluation` phase sourced
  from `source_library/evaluations/upstream/upstream_evaluation_results.json` and fail closed when
  that summary is missing or records `passed=false`
- closing commit hash:
  `d7c1f79` (`Implement upstream evaluation coverage milestone`)
- next routing boundary:
  execute `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md` next for retrieval, claim,
  rule-claim, and compliance-review direct-eval breadth
- affected dirty state:
  unrelated local changes already exist in `tests/test_nepa_3d_viewer.py`,
  `viewer/nepa-3d/app.js`, root-level East Crazies draft exports, and
  `docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf`; leave them out of the upstream
  milestone slice

Verification in this closeout:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_preflight.py tests/test_validate_run.py tests/test_catalog.py tests/test_extract.py tests/test_extraction_accuracy.py tests/test_upstream_evaluation.py tests/test_architecture_contract.py tests/test_cli.py tests/test_evidence_graph.py -q`: passed `105/105`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_evidence_graph.py tests/test_architecture_contract.py tests/test_cli.py -q`: passed `56/56` after the final lint-only cleanup in `evidence_graph.py`
- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md`: passed in the alignment follow-up
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json --results-dir source_library/evaluations/upstream`: passed with `matched_case_count=22`, `required_category_count=11`, and all lane summaries `direct_eval_present`
- `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library`: passed `8/8` with source set `source-set-5e65d845ce77e1a0`; `upstream_evaluation` was present and passing
- `git diff --check`: passed

Residual risks:

- downstream direct-eval breadth for retrieval, claim, rule-claim, and compliance-review remains a
  separate follow-on milestone
- the live upstream evaluation outputs are under ignored `source_library/`, so future sessions must
  regenerate them locally rather than expecting them in git history

## Downstream Direct Eval Strengthening Closeout

The downstream direct-eval strengthening milestone is now implemented across code, tracked
contracts, readiness wiring, and closeout docs.

- scope:
  `config/downstream_direct_eval_v1.json`, shipped contract-object seed files for retrieval,
  claims, rule-claim links, and compliance review, `src/usfs_r1_ea_sources/eval_metrics.py`,
  downstream lane owners, `src/usfs_r1_ea_sources/compliance_coverage.py`,
  `src/usfs_r1_ea_sources/evidence_graph.py`, focused tests, and the downstream register/state
  docs
- current direct-eval truth:
  the shipped downstream suites now require retrieval `12` cases with `3` hard negatives and `3`
  multi-source cases, claims `10` cases with `3` hard negatives and `3`
  multi-source-or-type-confusion cases, rule-claim links `24` cases with `4` hard negatives and
  `4` multi-source cases, and compliance review `5` cases with `1` all-authorities control, `2`
  unrelated-package hard negatives, and `2` conditional subsets
- live closeout replay:
  on `source-set-5e65d845ce77e1a0`, `retrieval-eval` passed `12/12`, `claim-eval` passed `10/10`,
  `rule-claim-eval` passed `24/24`, `compliance-review-eval` passed `5/5`,
  `compliance-coverage` passed with complete rule-pack/eval/link alignment, and source-set
  `phase-eval` passed `9/9` with `downstream_direct_evaluation` present and passing
- readiness integration:
  `phase-eval` now loads `config/downstream_direct_eval_v1.json`, verifies each required lane's
  eval ID, source set, contract hash, and pass status, and fails closed when a downstream result is
  missing, stale, or failing
- next routing boundary:
  execute `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md` next for adjudicated gold and
  multi-review real-package coverage
- affected dirty state:
  unrelated local changes already exist in `tests/test_nepa_3d_viewer.py`,
  `viewer/nepa-3d/app.js`, root-level East Crazies draft exports, and
  `docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf`; leave them out of the downstream
  milestone slice

Verification in this closeout:

- `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown`: passed with no Python/JS cycles and no new hotspot class introduced by the downstream milestone slice
- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md`: passed
- `PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py tests/test_claim_extraction.py tests/test_rule_claim_binding.py tests/test_compliance_review.py tests/test_downstream_direct_eval_contracts.py tests/test_architecture_contract.py`: passed `102/102`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed `12/12`
- `PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed `10/10`
- `PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed `24/24`
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed `5/5`
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library`: passed `9/9` with `reviewer_ready=true`
- `git diff --check`: passed

Residual risks:

- this milestone resolves shipped downstream direct-eval coverage and fail-closed readiness
  routing, but it does not itself widen adjudicated gold or multi-review real-package truth
- the live eval outputs remain under ignored `source_library/`, so future sessions must rerun the
  commands locally rather than expecting the result JSON files in git history

## Phase Eval Direct-Eval Gating Plan

The repo now has a dedicated follow-on plan for the `phase-eval` proxy-readiness gap at
`docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`.

- scope alignment:
  this is a fresh standalone milestone for making `phase-eval` consume explicit per-subsystem
  direct-eval summaries and fail closed on proxy-only or below-threshold coverage; it does not
  recreate the upstream, downstream, or gold eval suites that produce those summaries
- dependency:
  do not start this plan until `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md` is closed green and
  committed; that prerequisite itself depends on
  `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md`, which depends on
  `docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md`, so Sequence 0 of the new phase-eval plan
  assumes the upstream-created evaluation coverage register, the downstream direct-eval contracts,
  and the gold-coverage aggregate gate already exist
- problem statement:
  current `phase-eval` is a good readiness aggregator but still mostly trusts lane
  `validation_passed` and `reviewer_ready` bits for its critical source-set phases; the new plan
  adds one tracked direct-eval contract, normalized summary loading, explicit direct-eval failure
  reasons, and promotion checks that fail when critical phases are proxy-only or below their
  declared coverage floors
- routing:
  once the prerequisite milestone chain is complete, execute Sequence 0 from
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`; the first deliverables are
  `config/phase_eval_direct_eval_v1.json`, a focused direct-eval loader module, a `phase_eval`
  row in `docs/EVALUATION_COVERAGE_REGISTER.md`, and failing contract tests for missing
  direct-eval summaries or proxy-only critical phases
- affected dirty state:
  unrelated local changes already exist in `tests/test_nepa_3d_viewer.py`,
  `viewer/nepa-3d/app.js`, root-level East Crazies draft exports, and
  `docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf`; leave them out of the phase-eval
  planning and implementation slices

Verification in this planning pass:

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`: passed
- `git diff --check`: passed

Residual risks:

- this is a plan artifact only; the `phase-eval` gap remains open until the prerequisite milestone
  chain lands and this follow-on milestone is implemented end to end
- the plan assumes the prerequisite milestones produce machine-readable eval summaries or explicit
  contract-owned equivalents; if they close with different artifact names or missing threshold
  fields, Sequence 0 must refresh the routing before implementation begins

## Gold Coverage Expansion Plan

The repo now has a dedicated follow-on plan for the adjudicated gold and real-package coverage gap
at `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md`.

- scope alignment:
  this is a fresh standalone milestone for applicability gold, compliance gold, and multi-review
  real-package contract coverage; it does not reopen upstream capture/catalog/extraction or the
  downstream direct-eval ranking lane except to consume their completed register/readiness outputs
- dependency:
  do not start this plan until `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md` is
  closed green and committed; that prerequisite itself depends on
  `docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md`, so Sequence 0 of the new gold-coverage
  plan assumes the upstream-created `docs/EVALUATION_COVERAGE_REGISTER.md` and direct-eval-aware
  readiness route already exist
- problem statement:
  applicability gold and compliance gold exist, but adjudicated coverage is still narrow relative
  to the authority universe, and the default real-package V1 review contract is still East Crazies
  only; the new plan widens named family coverage for FLPMA, wetlands, MBTA, NHPA, roadless,
  tribal/cultural, and multi-forest plan triggers, and requires a three-review real-package set
- declared package surfaces:
  East Crazies intake path under
  `source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)`,
  West Reservoir via `config/replay_contexts/west-reservoir-67436.json`, and South Plateau intake
  path under `source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment`
- routing:
  once the downstream direct-eval milestone is complete, execute Sequence 0 from
  `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md`; the first deliverables are
  `config/gold_coverage_v1.json`, gold rows in `docs/EVALUATION_COVERAGE_REGISTER.md`, and failing
  contract tests for missing named-theme coverage or missing review diversity
- affected dirty state:
  unrelated local changes already exist in `tests/test_nepa_3d_viewer.py`,
  `viewer/nepa-3d/app.js`, root-level East Crazies draft exports, and
  `docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf`; leave them out of the gold-coverage
  slice

Verification in this planning pass:

- `git diff --check`: passed for the new plan and handoff updates

Residual risks:

- this is a plan artifact only; the gold-coverage gap remains open until the prerequisite
  downstream milestone lands and this follow-on milestone is implemented end to end
- West Reservoir remains partly dependent on an external package path, and South Plateau still has a
  typed forest-plan blocker; Sequence 0 must confirm those package authorities before implementation
  begins

## Downstream Direct Eval Strengthening Plan

The repo now has a dedicated follow-on plan for the downstream direct-eval gap at
`docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md`.

- scope alignment:
  this is a fresh standalone milestone for retrieval, claim, rule-claim, and compliance-review
  direct-eval strengthening; it does not reopen the upstream capture/catalog/extraction plan except
  to consume its register and readiness outputs
- dependency:
  do not start this plan until `docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md` is closed
  green and committed; Sequence 0 of the new plan explicitly assumes the upstream milestone already
  created `docs/EVALUATION_COVERAGE_REGISTER.md` and the direct-eval-aware readiness route
- problem statement:
  current downstream evals are permissive on "some relevant hit" and too thin on shipped coverage;
  the new plan requires contract-based default seeds, hard negatives, multi-source recall cases,
  rank-quality metrics, false-positive/missing-required-source rates, and downstream register/gate
  wiring
- routing:
  once the upstream milestone is complete, execute Sequence 0 from
  `docs/DOWNSTREAM_DIRECT_EVAL_STRENGTHENING_MILESTONE_PLAN.md`; the first deliverables are
  `config/downstream_direct_eval_v1.json`, downstream rows in
  `docs/EVALUATION_COVERAGE_REGISTER.md`, and failing contract tests for missing thresholds or thin
  coverage
- affected dirty state:
  unrelated local changes already exist in `config/applicability_adjudications/west-reservoir-67436.json`,
  `tests/test_nepa_3d_viewer.py`, `viewer/nepa-3d/app.js`, and root-level East Crazies draft
  exports; leave them out of the downstream-direct-eval slice

Verification in this planning pass:

- `git diff --check`: passed for the new plan and handoff updates

Residual risks:

- this is a plan artifact only; the downstream direct-eval gap remains open until the prerequisite
  upstream milestone lands and this follow-on milestone is implemented end to end
- the plan assumes the upstream milestone keeps the register/readiness artifact names described in
  its proposal; if those names change at closeout, Sequence 0 must refresh the routing before code
  work starts

## Region 1 Flathead Live-Package Proving Closeout Alignment

This addendum closes the remaining milestone-contract gaps from the original West Reservoir
closeout.

- proving surface:
  local West Reservoir package at `/Users/chunkstand/Downloads/West Reservoir (67436)`,
  review `west-reservoir-67436`,
  source set `source-set-5e65d845ce77e1a0`
- closing commit hash:
  the original Flathead live-package closeout landed in `1163a5e`
- tracked adjudication contracts:
  no new tracked adjudication file was added; existing
  `config/applicability_adjudications/west-reservoir-67436.json` was refreshed back to the current
  three-item replay contract after clean `applicability-determine` and
  `applicability-adjudication-template` reruns
- current reviewer-ready state:
  `applicability_validation.json` is green at `44` applicable and `23` non-applicable authorities
  with `0` unresolved and `0` `needs_adjudication`; the generated pack validates at `44` rules,
  `forest_plan_component_adjudication_eval.json` is green with `48` queue items, `48` resolved,
  and `0` pending, `compliance_gold_eval_results.json` passes `10/10` with
  `promotion_ready=true`, and review-bound `phase-eval` passes `17/17` with
  `reviewer_ready=true`
- next routing boundary:
  do not reopen West Reservoir unless a new regression appears; route future work to the next
  selected post-V1 expansion or promotion boundary

Verification in this alignment addendum:

- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-template --output-dir source_library --review-id west-reservoir-67436`: passed with `pending_item_count=48` and `queue_item_count=48`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id west-reservoir-67436 --adjudication-file config/forest_plan_component_adjudications/west-reservoir-67436.json`: passed with `48` resolved adjudications, `0` pending, and `reviewer_ready=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-5e65d845ce77e1a0`: passed with `41` applicable, `23` non-applicable, and `3` `needs_adjudication` decisions before replaying tracked adjudications
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-template --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-5e65d845ce77e1a0`: passed with `adjudication_item_count=3`
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-eval --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-5e65d845ce77e1a0 --adjudication-file config/applicability_adjudications/west-reservoir-67436.json`: passed with `3` resolved adjudications and `0` pending
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-apply --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-5e65d845ce77e1a0 --adjudication-file config/applicability_adjudications/west-reservoir-67436.json`: passed with `applied_item_count=3` and `remaining_unresolved_authority_count=0`
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-5e65d845ce77e1a0`: passed with `44` applicable, `23` non-applicable, `0` unresolved, `generated_rule_pack_ready=true`, and `reviewer_ready=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-5e65d845ce77e1a0`: passed with `generated_rule_count=44` and `generated_rule_pack_ready=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review --package-path '/Users/chunkstand/Downloads/West Reservoir (67436)' --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --review-id west-reservoir-67436 --forest-unit-id flathead-nf --rule-pack source_library/reviews/west-reservoir-67436/applicability/generated_rule_pack.json --reuse-package-cache`: passed with `validation_passed=true`, `reviewer_ready=true`, and `finding_status_counts={"gap":3,"pass":26,"uncertain":15}`
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --forest-unit-id flathead-nf --rule-pack source_library/reviews/west-reservoir-67436/applicability/generated_rule_pack.json --gold-file config/compliance_gold_eval_v0.json --results-dir source_library/reviews/west-reservoir-67436`: passed `10/10` with `promotion_ready=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id west-reservoir-67436`: passed `17/17` with `reviewer_ready=true`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py tests/test_forest_plan_resolver.py tests/test_forest_plan_component_adjudication.py tests/test_compliance_review.py tests/test_replay_context.py tests/test_cli.py tests/test_architecture_contract.py`: passed `172/172`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `git diff --check`: passed

Residual risks:

- the proving package remains outside the repo, so the replay-context contract and handoff still
  carry part of the durability boundary
- the refreshed applicability adjudication file is intentionally a pre-apply three-item contract;
  replay still depends on rerunning `applicability-adjudication-apply` before
  `applicability-validate`
- this still proves one real Flathead package, not every future Flathead EA package

## Upstream Evaluation Coverage Plan

The repo now has a dedicated plan for the upstream direct-eval gap at
`docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md`.

- scope alignment:
  this is a fresh standalone milestone for capture, catalog, and extraction evaluation coverage; it
  is not a rewrite of the broader V1, NEPA 3D, or post-V1 expansion lanes
- problem statement:
  current upstream truth is stronger on validation than on direct eval; the new plan requires
  tracked adversarial coverage for challenge pages, deceptive `200` responses, duplicate
  URL/content cases, override drift, batch/catalog mismatches, OCR-heavy PDFs, tables, appendices,
  and section-boundary extraction
- routing:
  execute Sequence 0 from `docs/UPSTREAM_EVALUATION_COVERAGE_MILESTONE_PLAN.md` before adding any
  new upstream eval command or readiness wiring; the first deliverables are the tracked eval
  manifest and evaluation coverage register
- affected dirty state:
  unrelated local changes already exist in `config/applicability_adjudications/west-reservoir-67436.json`,
  `tests/test_nepa_3d_viewer.py`, `viewer/nepa-3d/app.js`, and root-level East Crazies draft
  exports; leave them out of the upstream-evaluation slice

Verification in this planning pass:

- `git diff --check`: passed for the new plan and handoff updates

Residual risks:

- this is a plan artifact only; the direct-eval gap remains open until the implementation milestone
  lands and the new aggregate gate is green

## Region 1 Flathead Live-Package Proving Closeout

The West Reservoir proving lane is now closed green on the active full-canonical corpus.

- proving surface:
  local West Reservoir package at `/Users/chunkstand/Downloads/West Reservoir (67436)`,
  review `west-reservoir-67436`,
  source set `source-set-5e65d845ce77e1a0`
- outcome:
  review-bound `phase-eval` now passes `17/17` with `reviewer_ready=true`, so Flathead now has a
  real live-package reviewer-ready proving review on the active source set
- applicability and generated pack:
  `applicability_validation.json` now reports `44` applicable authorities, `23`
  non-applicable authorities, `0` unresolved, `0` `needs_adjudication`, and
  `generated_rule_pack_ready=true`; `generated_rule_pack_validation.json` passes with `44` rules
- forest-plan proving:
  `forest_plan_context_validation.json` is green with `scope_status="flathead_nf"`, and
  `forest_plan_component_adjudication_eval.json` now passes with `48` queue items,
  `48` resolved adjudications, `0` pending, and `reviewer_ready=true`
- review and gold:
  `compliance_review.json` is green in generated-pack mode with
  `finding_status_counts={"pass":26,"uncertain":15,"gap":3}`, and
  `compliance_gold_eval_results.json` passes `10/10` cases with `promotion_ready=true`
- generic code fixes closed in this lane:
  Flathead supporting-plan evidence now closes against support-scoped catalog records,
  review-local generated-pack gold eval now accepts base-gold contracts with generated overrides,
  and the authority-universe gate no longer treats the Region 1 aggregate component inventory as a
  profile-scoped applicability input
- next step:
  do not reopen the Flathead live-package lane unless a new regression appears; route future work
  to the next selected post-V1 expansion or promotion boundary

Verification in this closeout:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability.py tests/test_architecture_contract.py`: passed `12/12`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `git diff --check`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-5e65d845ce77e1a0`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-5e65d845ce77e1a0`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-5e65d845ce77e1a0`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review --package-path '/Users/chunkstand/Downloads/West Reservoir (67436)' --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --review-id west-reservoir-67436 --forest-unit-id flathead-nf --rule-pack source_library/reviews/west-reservoir-67436/applicability/generated_rule_pack.json --reuse-package-cache`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --forest-unit-id flathead-nf --rule-pack source_library/reviews/west-reservoir-67436/applicability/generated_rule_pack.json --gold-file config/compliance_gold_eval_v0.json --results-dir source_library/reviews/west-reservoir-67436`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id west-reservoir-67436`: passed `17/17`, `reviewer_ready=true`

Residual risks:

- the proving package remains outside the repo, so the replay-context contract and this handoff
  remain part of the durability boundary
- this closes one real Flathead proving review, not every future Flathead package; future package
  replays still need their own evidence-backed runs

## Region 1 Flathead Live-Package Proving Plan

The remaining Flathead work is now formalized in
`docs/R1_FLATHEAD_LIVE_PACKAGE_PROVING_MILESTONE_PLAN.md`.

- scope alignment:
  the Flathead profile-expansion milestone is already closed; this new plan is only for the
  remaining live-package proof gap
- declared proving surface:
  local West Reservoir package at `/Users/chunkstand/Downloads/West Reservoir (67436)`,
  review `west-reservoir-67436`,
  source set `source-set-5e65d845ce77e1a0`
- current baseline truth:
  package checklist is green, but review-bound `phase-eval` is still red at `11/16` phases passed
- current typed blockers:
  `3` unresolved applicability families,
  `6` Flathead supporting-plan routes missing source-backed closure,
  `80` component-adjudication queue items, and stale/non-reviewer-ready review-local gold alignment
- next step:
  execute Sequence 0 from `docs/R1_FLATHEAD_LIVE_PACKAGE_PROVING_MILESTONE_PLAN.md`, then close
  applicability before touching component adjudication or review-local gold alignment

Verification in this planning pass:

- `git diff --check`: passed

Residual risks:

- the current proving package lives outside the repo, so the replay-context contract and handoff
  must keep the package boundary explicit
- this plan is narrower than the broader next-forest expansion lane; it should not be widened into
  roster-level work

## Forest Plan Component Source-Text Accuracy Closeout

Forest-plan component verification is now tightened against the live source documents and extracted
text on the active full-canonical source set.

- outcome:
  `forest-plan-components-build` now fails closed unless each emitted component can be traced to a
  canonical primary source chunk with the expected `source_record_id`, `artifact_sha256`, and
  `content_sha256`, and unless reparsing that canonical chunk re-emits the same component from the
  extracted text
- implementation note:
  overlapping merged component records now keep canonical chunk ordering stable, which closes the
  earlier ambiguity where a merged component could carry the right text/hash but point evidence at a
  shorter non-canonical chunk
- proving surface:
  the live active build on `source-set-5e65d845ce77e1a0` now records
  `component_source_accuracy_passed=true` and `component_source_accuracy_failure_count=0`; a
  targeted Flathead probe over the live inventory also passed with `80` components, `20`
  standards, and `0` primary-chunk accuracy failures
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_compliance_review.py tests/test_forest_plan_resolver.py`,
  `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_nepa_knowledge_graph_export.py`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src python -m compileall src`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`,
  and `git diff --check` passed in this closeout pass
- next step:
  keep this source-text accuracy gate as part of the standard active-source-set component replay,
  then treat future forest-profile or review promotions as separate proving lanes rather than
  assuming component/source-document fidelity from inventory counts alone

## Region 1 Flathead Direct Extraction Admission Closeout

The Flathead source-document extraction gap from the last pass is now closed on the active source
set.

- outcome:
  all `17` required `R1PLAN-flathead-nf-01..17` records were re-extracted directly from the active
  local source artifacts into `source-set-5e65d845ce77e1a0`, the targeted accuracy audit admitted
  all `17` required records with `0` blocked, and retrieval now records the Flathead verified
  extraction contract before knowledge-base admission
- proving surface:
  this is stronger than the prior tracked-fixture-only extraction story because it uses the live
  local source documents on `source-set-5e65d845ce77e1a0`; however, it still does not replace the
  separate need for a live Flathead EA package replay
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_extract.py tests/test_extraction_accuracy.py tests/test_retrieval.py tests/test_cli.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src python -m compileall src`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources extract-build --output-dir source_library --merge-selected-into-existing --id R1PLAN-flathead-nf-01 --id R1PLAN-flathead-nf-02 --id R1PLAN-flathead-nf-03 --id R1PLAN-flathead-nf-04 --id R1PLAN-flathead-nf-05 --id R1PLAN-flathead-nf-06 --id R1PLAN-flathead-nf-07 --id R1PLAN-flathead-nf-08 --id R1PLAN-flathead-nf-09 --id R1PLAN-flathead-nf-10 --id R1PLAN-flathead-nf-11 --id R1PLAN-flathead-nf-12 --id R1PLAN-flathead-nf-13 --id R1PLAN-flathead-nf-14 --id R1PLAN-flathead-nf-15 --id R1PLAN-flathead-nf-16 --id R1PLAN-flathead-nf-17`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --contract-path config/verified_extraction_admission_contract.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`,
  and `git diff --check` all passed on 2026-05-12
- current live state:
  `extraction_accuracy_audit` now reports `audited_record_count=17`,
  `knowledge_base_admitted_source_record_ids=17`, and
  `knowledge_base_blocked_source_record_ids=[]`; retrieval reports
  `verified_extraction_contract_ids=["flathead-forest-plan-direct-extraction"]`,
  `verified_extraction_required_source_count=17`, and
  `verified_extraction_admitted_source_count=17`
- next step:
  keep the Flathead source-backed extraction gate in place, then treat any future Flathead
  promotion from here as a separate live-package proving lane rather than reopening extraction reuse

## Region 1 Flathead Profile Expansion Closeout

The Flathead single-forest profile-expansion milestone is now implemented.

- outcome:
  `flathead-nf` is now a configured Milestone 5 added active profile, the tracked profile owns all
  `17` Flathead register rows, and the selected-profile resolver/compliance path now proves
  district, geographic-area, focused-recreation, overlay, currentness, and supporting-route depth
- proving surface:
  closeout used tracked Flathead proving fixtures in
  `tests/test_forest_plan_resolver.py` and `tests/test_compliance_review.py`; this milestone is
  verified, but it is still weaker than a live local Flathead EA package replay
- verification:
  `python -m json.tool config/forest_plan_profiles.json`,
  `python -m json.tool config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_cli.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src python -m compileall src`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`,
  and `git diff --check` all passed on 2026-05-11
- downstream alignment:
  the live graph export now reports `region1_forest_plan_graph_ready_profile_count=10`,
  `region1_forest_plan_added_profile_count=2`,
  `region1_forest_plan_added_profiles_with_eval_fixture_count=2`, and
  `region1_forest_plan_blocked_profile_count=0`
- next step:
  route to the next selected remaining non-Custer forest-specific expansion lane, preserving the
  distinction between tracked-fixture proof and live-package proof

## Region 1 Flathead Single-Forest Profile Expansion Plan

The next active single-forest expansion lane is now formalized in
`docs/R1_FLATHEAD_PROFILE_EXPANSION_MILESTONE_PLAN.md`.

- scope alignment:
  this plan is narrower than the retired multi-forest lane and narrower than the Beaverhead
  reference artifact; it targets Flathead only and explicitly includes the remaining work needed to
  complete the Flathead forest plan plus all tracked Flathead supporting/currentness documents for a
  reviewer-ready review path
- current Flathead state:
  the live Flathead inventory is already validated at `80` components and `20` standards on active
  source set `source-set-5e65d845ce77e1a0`, the primary plan is already promoted to
  `document_role=forest_plan`, and isolated single-forest inventory proof already passed; however,
  Flathead still sits at `profile_kind=region1_tracking_only`, `applicability_eval_coverage.status=not_started`,
  empty district/geography/management-area/overlay/trigger arrays, and only `10` explicit source
  roles in `config/forest_plan_profiles.json`
- completeness alignment:
  the new plan treats the full Flathead register as the authoritative support-document contract:
  `17` tracked rows total, with the current omitted profile roles called out explicitly
  (`08`, `09`, `11`, `13`, `14`, `15`, `17`)
- gate alignment:
  the milestone now requires register-backed profile completeness, Flathead resolver depth,
  Flathead selected-profile compliance and CLI parity, a Flathead EA proving review path, and the
  mandatory all-R1 `forest-plan-components-build` replay plus live
  `nepa-knowledge-graph-export` before closeout

Immediate next step if this lane is continued:

1. Execute Sequence 0 from `docs/R1_FLATHEAD_PROFILE_EXPANSION_MILESTONE_PLAN.md`, starting with
   the failing Flathead completeness and proving-package contract.

Verification in this pass:

- `git diff --check`: passed

Residual risks:

- no tracked Flathead reviewer-ready proving fixture or package is yet identified in the repo, so
  the new plan keeps that as an explicit gate and stop condition rather than assuming it exists
- older append-only handoff sections still describe Beaverhead as the newest active expansion
  routing, so future sessions must follow this Flathead section when those older notes conflict

## Region 1 Beaverhead Single-Forest Profile Expansion Plan

The prior multi-forest expansion plan has been retired in favor of a Beaverhead-specific reference
milestone at `docs/R1_BEAVERHEAD_PROFILE_EXPANSION_MILESTONE_PLAN.md`.

- scope alignment:
  Beaverhead-Deerlodge is now the documented single-forest reference slice, and future non-Custer
  expansion work should create one forest-specific milestone plan at a time instead of widening a
  roster-level plan
- gate alignment:
  the Beaverhead plan preserves the gate-first sequence: profile completeness contract, config
  depth, resolver proofs, compliance-gate parity, and mandatory all-R1
  `forest-plan-components-build` verification before closeout
- routing alignment:
  `docs/R1_MULTI_FOREST_PROFILE_EXPANSION_MILESTONE_PLAN.md` is now only a retired routing note,
  not an active implementation plan

Immediate next step if this lane is continued:

1. Pick the next single forest and write a new forest-specific milestone plan using
   `docs/R1_BEAVERHEAD_PROFILE_EXPANSION_MILESTONE_PLAN.md` as the baseline contract.

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_cli.py tests/test_architecture_contract.py`: passed `143/143`
- `git diff --check`: passed

Residual risks:

- Beaverhead is now the documented reference slice, but the remaining non-Custer forests still need
  their own forest-specific milestone files rather than ad hoc expansion under Beaverhead
- older append-only handoff sections still mention the retired multi-forest plan, so future
  sessions must follow the newest Beaverhead routing section when those older notes conflict

## Region 1 Multi-Forest Profile Expansion Plan

The next post-V1 expansion lane is now formalized in
`docs/R1_MULTI_FOREST_PROFILE_EXPANSION_MILESTONE_PLAN.md`.

- scope alignment:
  the plan is narrowly scoped to enriching the remaining non-Custer
  `config/forest_plan_profiles.json` entries to Beaverhead-level review depth, preserving the
  default Custer path, and proving selected-profile resolver/compliance behavior without reopening
  parser, catalog, or replay work
- gate alignment:
  the plan requires a gate-first Sequence 0 profile-depth contract, then config-driven vocabulary
  expansion, selected-profile resolver/compliance regressions, and a mandatory all-R1
  forest-plan verification replay before closeout
- closeout rule:
  the milestone cannot close from unit tests alone; it must rerun
  `forest-plan-components-build --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  on active source set `source-set-5e65d845ce77e1a0` and validate all `10` tracked Region 1 forest
  plans before docs, handoff, and commit closeout are allowed

Immediate next step if this lane is continued:

1. Execute Sequence 0 from `docs/R1_MULTI_FOREST_PROFILE_EXPANSION_MILESTONE_PLAN.md`, then move
   into the first profile-family config expansion only after the roster-level completeness gate is
   failing or fully defined.

## Region 1 Non-Custer Review Gate Expansion

The first non-Custer reviewer-ready forest-plan review slice is now implemented and verified for
Beaverhead-Deerlodge without breaking the long-lived default Custer contract.

- profile/config alignment:
  `config/forest_plan_profiles.json` still carries explicit profiles for all `10` tracked
  readiness units, and the Beaverhead-Deerlodge profile now adds tracked district, landscape,
  management-area, overlay, and supporting-route vocabularies grounded in the active local BDNF
  plan, FEIS, ROD, and ESA support records
- compliance-path alignment:
  `run_compliance_review(...)` now threads explicit forest-plan profile selection into
  `run_forest_plan_resolver(...)`, and `compliance-review`, `compliance-review-eval`, plus
  `compliance-gold-eval` now accept `--forest-unit-id` and `--forest-plan-profiles-path`
- gate alignment:
  `forest_plan_component_gate_reviewer_ready` is no longer hard-coded to
  `scope_status="custer_gallatin"`; any explicitly selected in-scope profile now has to clear the
  reviewer-ready component/adjudication gate, while ambiguous and out-of-scope packages still keep
  the gate non-required
- proving coverage:
  focused tests now prove a Beaverhead-selected compliance review resolves `scope_status` to
  `beaverhead_deerlodge_nf`, resolves Dillon District plus Big Hole / West Big Hole / IRA context,
  routes FEIS/ROD/ESA supporting evidence, and fails closed unless the selected profile’s forest
  plan component gate is reviewer-ready

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_architecture_contract.py`: passed `143/143`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `python -m json.tool config/forest_plan_profiles.json >/dev/null`: passed
- `git diff --check`: passed

Residual risks:

- the default resolver/compliance path still centers Custer Gallatin unless a non-default
  `forest_unit_id` is selected explicitly
- Beaverhead is now the first non-Custer reviewer-ready path, but the remaining non-Custer
  profiles still mostly stop at source-record readiness and need their own richer
  district/area/overlay/trigger authoring
- this pass generalized the gate and one proving profile; it did not yet prove reviewer-ready
  package review across the rest of the Region 1 roster

Immediate next step if this slice is continued:

1. Repeat the Beaverhead profile-depth pattern across the next non-Custer units, then prove those
   richer profiles through selected real package reviews before claiming broader any-R1 reviewer
   readiness.

## Region 1 Resolver Profile Expansion

The next any-R1-review capability slice is now implemented in tracked config, but it does not yet
generalize reviewer-ready forest-plan review beyond the long-lived Custer Gallatin path.

- profile/config alignment:
  `config/forest_plan_profiles.json` now contains explicit resolver-profile entries for all `10`
  tracked readiness units instead of only Custer Gallatin plus the earlier Beaverhead expansion
  slice
- source-contract alignment:
  the new non-Custer profiles flatten readiness-contract multi-record document families into
  tracked per-part source roles, so the resolver can now carry the full source-record readiness
  contract for Beaverhead-Deerlodge, Bitterroot, Dakota Prairie, Flathead,
  Helena-Lewis-and-Clark, Idaho Panhandle, Kootenai, Lolo, and Nez Perce-Clearwater without
  hiding source lists in Python
- preserved limitation:
  most newly expanded profiles still have empty district, geographic-area, management-area, overlay,
  and supporting-trigger vocabularies, so this pass does not by itself make non-Custer packages
  reviewer-ready; it makes the resolver-profile ownership surface complete and explicit
- docs/state alignment:
  README and current-state docs now distinguish full profile coverage from the still-open work of
  authoring per-forest geography/overlay/trigger vocabularies and generalizing the non-Custer
  review gate

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_forest_plan_source_delta_readiness.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py`: passed `58/58`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `python -m json.tool config/forest_plan_profiles.json >/dev/null`: passed

Residual risks:

- the default resolver path still preserves the Custer Gallatin V0 scope contract
- non-Custer profiles now have tracked source-record readiness contracts, but they still lack the
  richer location and supporting-route vocabularies needed for Custer-level review depth
- compliance validation still treats Custer Gallatin as the only scope that currently requires the
  full forest-plan reviewer-ready gate

Immediate next step if this slice is continued:

1. Author the first non-Custer profile vocabularies and supporting-plan routes, then generalize the
   forest-plan review gate away from the Custer-only assumption.

## Region 1 Forest-Plan Parser Recovery Closeout

The active full-canonical forest-plan inventory lane on `source-set-5e65d845ce77e1a0` now closes
the final Dakota Prairie and Lolo parser blockers without reopening stale-surface work or
weakening duplicate-ID protection.

- parser/runtime alignment:
  manifest-selected component-bearing plan chunks now parse even when their catalog
  `document_role` is `forest_plan_support`; legacy period-numbered forms such as `Standard 2.` and
  `Guideline 7.` now resolve as plan components; `Standard No. 21.` style headings now parse; and
  period-style legacy IDs now use longer body context plus a deterministic short text digest so
  repeated numbered headings do not collapse onto the same identifier
- regression coverage:
  `tests/test_forest_plan_components.py` now proves period-numbered legacy items, `Standard No.`
  headings, and manifest-selected `forest_plan_support` primary-plan chunks all build component
  inventory correctly
- live full-canonical outcome:
  `forest-plan-components-build --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  on `source-set-5e65d845ce77e1a0` now validates all `10` tracked forests:
  `custer-gallatin-nf` (`329/58`), `beaverhead-deerlodge-nf` (`90/89`), `bitterroot-nf` (`23/3`),
  `dakota-prairie-grasslands` (`394/161`), `flathead-nf` (`80/20`),
  `helena-lewis-and-clark-nf` (`258/28`), `idaho-panhandle-nfs` (`52/8`),
  `kootenai-nf` (`53/8`), `lolo-nf` (`1/1`), and `nez-perce-clearwater-nfs` (`136/21`)
- readiness/graph alignment:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` now promotes all `10` validated
  inventories with no remaining active parser blockers; active
  `nepa-knowledge-graph-export` now passes with `66` checks, `0` failed, `2,850` nodes,
  `6,086` edges, `region1_forest_plan_graph_ready_profile_count=10`, and
  `region1_forest_plan_blocked_profile_count=0`
- promotion truth remains unchanged at the high level:
  `promotion-suite` still reports `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `promotion_ready=true`, and `expansion_ready=false`

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_nepa_knowledge_graph_export.py`: passed `38/38`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_inventory_build_manifest.py tests/test_architecture_contract.py`: passed `13/13`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`: passed with `10` validated forests, `0` blocked forests, `1416` components, and `397` standards
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `66` checks, `0` failed, `2,850` nodes, and `6,086` edges
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`: passed with `current_promotion_ready=true`, `full_canonical_corpus_ready=true`, `promotion_ready=true`, and `expansion_ready=false`

Residual risks:

- the active full-canonical parser lane is closed, but `promotion-suite` still reports
  `expansion_ready=false`
- the remaining work is the separate post-V1 expansion lane, currently surfaced as
  `forest_plan_reviewer_not_ready` counts in expansion reporting

Immediate next step if this slice is continued:

1. Move to the post-V1 expansion lane; do not reopen active full-canonical parser recovery unless
   the newly green inventory surfaces drift.

## Region 1 Beaverhead Duplicate-ID Closeout

The active full-canonical forest-plan inventory lane on `source-set-5e65d845ce77e1a0` now closes
the Beaverhead duplicate-ID blocker without reopening stale-surface work.

- parser/runtime alignment:
  `forest_plan_components.py` now treats generic legacy section headings such as chapter headings
  and `Objectives None` as insufficient ID context for colon-number components, and falls back to
  body-derived legacy codes instead of collapsing distinct `Standard 1:` records onto
  `THREE-STD-1` or `NONE-STD-1`
- regression coverage:
  `tests/test_forest_plan_components.py` now proves Beaverhead-style generic legacy headings do
  not emit duplicate standard IDs across distinct colon-number standards
- live full-canonical outcome:
  `forest-plan-components-build --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  on `source-set-5e65d845ce77e1a0` now validates `8` forests:
  `custer-gallatin-nf` (`329/58`), `beaverhead-deerlodge-nf` (`88/88`), `bitterroot-nf` (`9/2`),
  `flathead-nf` (`80/20`), `helena-lewis-and-clark-nf` (`257/28`),
  `idaho-panhandle-nfs` (`52/8`), `kootenai-nf` (`53/8`), and
  `nez-perce-clearwater-nfs` (`134/21`)
- remaining blockers are narrower and explicit:
  only `dakota-prairie-grasslands` and `lolo-nf` still fail on
  `plan_component_labels_not_detected` plus `plan_standard_labels_not_detected`
- readiness/graph alignment:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` now promotes `8` validated inventories
  and keeps `2` blockers explicit; active `nepa-knowledge-graph-export` now passes with `66`
  checks, `0` failed, `2,448` nodes, `4,856` edges,
  `region1_forest_plan_graph_ready_profile_count=8`, and
  `region1_forest_plan_blocked_profile_count=2`
- promotion truth remains unchanged at the high level:
  `promotion-suite` still reports `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `promotion_ready=true`, and `expansion_ready=false`

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py`: passed `31/31`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_inventory_build_manifest.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py`: passed `18/18`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`: stopped as intended with `8` validated forests, `2` blocked forests, `1002` components, and `233` standards
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`: passed with `full_canonical_corpus_ready=true`

Residual risks:

- `dakota-prairie-grasslands` still needs legacy section-scoped parser recovery before it can emit
  component inventory labels
- `lolo-nf` still needs legacy section-scoped parser recovery before it can emit component
  inventory labels

Immediate next step if this slice is continued:

1. Implement the next legacy section-scoped parser pass for Dakota Prairie and Lolo so the final
   two blocked forests can close without weakening the current duplicate-ID gates.

## Region 1 Forest-Plan Parser Recovery Narrowed Active Blockers

The active full-canonical forest-plan inventory lane on `source-set-5e65d845ce77e1a0` now closes a
meaningful parser-recovery slice without reopening stale-surface work.

- parser/runtime alignment:
  `forest_plan_components.py` now recognizes two additional live plan-component formats that were
  blocking current Region 1 plans: explicit code-style headings such as
  `Desired Conditions FW-DC-...-01.` and legacy colon-number forms such as `Standard 1: ...`
- build-input hardening:
  manifest-driven inventory builds now parse component-bearing roles only
  (`primary_land_management_plan`, multipart primary-plan parts, amendments, and administrative
  changes) instead of every `forest_plan`-role supporting artifact tied to a profile
- live full-canonical outcome:
  `forest-plan-components-build --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  on `source-set-5e65d845ce77e1a0` now validates `7` forests:
  `custer-gallatin-nf` (`329/58`), `bitterroot-nf` (`9/2`), `flathead-nf` (`80/20`),
  `helena-lewis-and-clark-nf` (`257/28`), `idaho-panhandle-nfs` (`52/8`), `kootenai-nf` (`53/8`),
  and `nez-perce-clearwater-nfs` (`134/21`)
- remaining blockers are narrower and explicit:
  `beaverhead-deerlodge-nf` now fails on `duplicate_component_ids_detected` plus
  `duplicate_standard_ids_detected`; `dakota-prairie-grasslands` and `lolo-nf` still fail on
  `plan_component_labels_not_detected` plus `plan_standard_labels_not_detected`
- readiness/graph alignment:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` now promotes `7` validated inventories
  and keeps `3` blockers explicit; `config/nepa_3d_graph_contract_v1.json` and
  `nepa_3d_graph_contract.py` now recognize duplicate-ID blocker classes; active
  `nepa-knowledge-graph-export` now passes with `66` checks, `0` failed, `2,451` nodes,
  `4,853` edges, `region1_forest_plan_graph_ready_profile_count=7`, and
  `region1_forest_plan_blocked_profile_count=3`
- promotion truth remains unchanged at the high level:
  `promotion-suite` still reports `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `promotion_ready=true`, and `expansion_ready=false`

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_forest_plan_inventory_build_manifest.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py`: passed `48/48`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`: stopped as intended with `7` validated forests, `3` blocked forests, `1003` components, and `234` standards
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`: passed with `full_canonical_corpus_ready=true`

Residual risks:

- `beaverhead-deerlodge-nf` still needs duplicate-ID disambiguation inside the 2009 plan parser
  path before it can be promoted
- `dakota-prairie-grasslands` and `lolo-nf` still need additional legacy section-scoped parsing
  before they will emit component inventories

Immediate next step if this slice is continued:

1. Resolve the Beaverhead duplicate-ID path first, then add the next legacy section-scoped parser
   pass for Dakota Prairie and Lolo so the remaining `3` blocked forests can close without
   weakening duplicate-ID gates.

## Replay Compliance And Gold Alignment Closeout

The last two East Crazies replay-repair slices are now aligned and closed for archived review lane
`v1-cg-ecid-source-delta-review`.

- forest-plan gate alignment:
  completed replay component adjudications no longer block `compliance_review` merely because the
  resolved dispositions are classified as `system_miss`; the miss counts remain explicit in
  `forest_plan_context_summary.json` and `compliance_validation.json`, but a completed reviewed
  adjudication path now counts as reviewer-ready
- gold-contract alignment:
  `config/compliance_gold_eval_v0.json` now includes the four current land-exchange rules, so the
  review-local gold rerun covers the full current base rule pack instead of failing closed on stale
  rule coverage
- live replay outcome:
  replay `compliance_review` is now reviewer-ready, the review-local gold eval now passes `10/10`
  adjudicated cases for `source-set-8a4005c8a083af1a`, and
  `phase-eval --review-id v1-cg-ecid-source-delta-review` now passes `18/18` with
  `reviewer_ready=true`

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py -k 'custer_component_adjudication or compliance_gold_eval'`: passed `10/10`
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review --package-path 'source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)' --output-dir source_library --review-id v1-cg-ecid-source-delta-review --source-set-id source-set-8a4005c8a083af1a --rule-pack source_library/reviews/v1-cg-ecid-source-delta-review/applicability/generated_rule_pack.json --reuse-package-cache`: passed with replay `compliance_validation.json` green and `reviewer_ready=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --source-set-id source-set-8a4005c8a083af1a --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --gold-file config/compliance_gold_eval_v0.json --results-dir source_library/reviews/v1-cg-ecid-source-delta-review`: passed with `10/10` cases and review-local `compliance_gold_eval_results.json`
- `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-source-delta-review`: passed `18/18` with `reviewer_ready=true`

Residual risks:

- the reviewed replay still records `system_miss_count=6` in the component adjudication summary; that is now an accepted reviewed-resolution signal rather than a readiness blocker
- the replay lane is green, but those six typed misses still describe real system-improvement opportunities if we later want the component findings themselves, not just the reviewed adjudication path, to go green without operator resolution

Immediate next step if this slice is continued:

1. Treat the archived replay lane as closed and move back to the active promotion or expansion lanes; do not reopen replay repair unless the archived artifacts drift.

## Replay Compliance Regeneration And Review-Local Gold Preference

The next East Crazies replay-repair slice is now implemented for archived review lane
`v1-cg-ecid-source-delta-review`.

- new replay-safe gold behavior:
  `phase-eval --review-id <review-id>` now prefers
  `source_library/reviews/<review_id>/compliance_gold_eval_results.json` when that review-local
  gold artifact exists, instead of always reading the unrelated global
  `source_library/reviews/compliance_gold_eval/compliance_gold_eval_results.json`
- live replay outcome:
  replay-scoped compliance regeneration now writes
  `source_library/reviews/v1-cg-ecid-source-delta-review/compliance_review.json` plus
  `source_library/reviews/v1-cg-ecid-source-delta-review/compliance_gold_eval_results.json`, and
  review-bound `phase-eval` now reads that local gold artifact rather than failing on the proving
  lane's stale source-set binding
- preserved non-goal boundary:
  this pass did not repair the stale gold adjudication contract itself and did not close the
  replay compliance review's embedded forest-plan gate

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py -k 'compliance_gold_eval or review_phase_eval_prefers_review_scoped_compliance_gold_eval'`: passed `8/8`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_evidence_graph.py -k 'gold_eval or unrelated_gold_eval'`: passed `1/1`
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review --package-path 'source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)' --output-dir source_library --review-id v1-cg-ecid-source-delta-review --source-set-id source-set-8a4005c8a083af1a --rule-pack source_library/reviews/v1-cg-ecid-source-delta-review/applicability/generated_rule_pack.json --reuse-package-cache`: wrote replay-scoped compliance artifacts; summary remained `reviewer_ready=false`
- `PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --source-set-id source-set-8a4005c8a083af1a --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --gold-file config/compliance_gold_eval_v0.json --results-dir source_library/reviews/v1-cg-ecid-source-delta-review`: wrote review-local gold artifacts but failed closed because the tracked gold file is stale for the current base rule pack
- `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-source-delta-review`: failed closed at `16/18`; blockers are now the replay-local `compliance_gold_eval` contract and replay `compliance_review`, not a global gold source-set mismatch

Residual risks:

- `config/compliance_gold_eval_v0.json` no longer covers the current base rule-pack shape; live failure details show missing land-exchange rule expectations and stale status-count expectations
- replay `compliance_review` still fails `forest_plan_component_gate_reviewer_ready`; the rerun writes matrix/PDF/validation artifacts, but `compliance_validation.json` still records `system_miss_adjudication` from the six replay component adjudications

Immediate next step if this slice is continued:

1. Repair or supersede the stale compliance-gold adjudication contract so the review-local gold eval can pass against the current base/generated rule-pack pair.
2. Decide whether the six replay forest-plan `system_miss` adjudications should be converted into true repair work or a reviewed acceptance path; until that changes, replay `compliance_review` remains non-reviewer-ready.
3. Rerun `phase-eval --review-id v1-cg-ecid-source-delta-review`.

## Replay Forest-Plan Component Closeout

The next East Crazies replay-repair slice is now implemented for archived review lane
`v1-cg-ecid-source-delta-review`.

- tracked replay forest-plan component authority:
  `config/forest_plan_component_evals/v1-cg-ecid-source-delta-review.json` now owns the replay
  component eval contract for archived merged source set `source-set-8a4005c8a083af1a`, and
  `config/forest_plan_component_adjudications/v1-cg-ecid-source-delta-review.json` now owns the
  six replay-scoped reviewer adjudications for the open component queue
- live replay outcome:
  replaying those tracked contracts writes a passing
  `forest_plan_component_eval_results.json`, writes a passing
  `forest_plan_component_adjudication_eval.json`, and moves review-scoped `phase-eval` from
  `14/17` to `16/18`
- preserved non-goal boundary:
  this pass did not regenerate replay-scoped `compliance_review` artifacts and did not refresh the
  replay `compliance_gold_eval` source-set binding

Verification in this pass:

- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id v1-cg-ecid-source-delta-review --eval-file config/forest_plan_component_evals/v1-cg-ecid-source-delta-review.json`: passed with `36/36` cases and `0` failed checks
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id v1-cg-ecid-source-delta-review --adjudication-file config/forest_plan_component_adjudications/v1-cg-ecid-source-delta-review.json`: passed with `6` resolved adjudications, `0` pending, and `0` expectation mismatches
- `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-source-delta-review`: failed closed as expected at `16/18`; remaining blockers are `compliance_gold_eval` and `compliance_review`

Residual risks:

- the replay is still `reviewer_ready=false`; only replay-scoped compliance regeneration remains
- `compliance_gold_eval` is still bound to proving-lane source set `source-set-ba8d0feae79501b8`
- replay `compliance_review` artifacts are still absent under
  `source_library/reviews/v1-cg-ecid-source-delta-review/`

Immediate next step if this slice is continued:

1. Regenerate replay-scoped `compliance_review` artifacts for
   `v1-cg-ecid-source-delta-review`.
2. Refresh replay-scoped compliance-gold evidence to remove the remaining `source_set_mismatch`.
3. Rerun `phase-eval --review-id v1-cg-ecid-source-delta-review`.

## Replay Applicability Adjudication Closeout

The next East Crazies replay-repair slice is now implemented for archived review lane
`v1-cg-ecid-source-delta-review`.

- tracked replay adjudication authority:
  `config/applicability_adjudications/v1-cg-ecid-source-delta-review.json` now owns the `7`
  replay-specific applicability adjudications for archived merged source set
  `source-set-8a4005c8a083af1a`
- regression coverage:
  `tests/test_applicability_decisions.py` now proves `applicability-adjudication-eval` and
  `applicability-adjudication-apply` accept a minimal external adjudication contract outside
  `source_library/`
- live replay outcome:
  replaying the tracked contract closed all `7` prior applicability conflicts, refreshed
  `applicable_authorities.json` / `non_applicable_authorities.json`, regenerated a `56`-rule
  `generated_rule_pack.json`, and moved review-scoped `phase-eval` from `12/17` to `14/17`
- preserved non-goal boundary:
  this pass did not repair East Crazies forest-plan component findings and did not regenerate
  replay-scoped compliance review or compliance gold-eval artifacts

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-eval --output-dir source_library --review-id v1-cg-ecid-source-delta-review --source-set-id source-set-8a4005c8a083af1a --adjudication-file config/applicability_adjudications/v1-cg-ecid-source-delta-review.json`: passed with `7` resolved adjudications and `0` pending
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-apply --output-dir source_library --review-id v1-cg-ecid-source-delta-review --source-set-id source-set-8a4005c8a083af1a --adjudication-file config/applicability_adjudications/v1-cg-ecid-source-delta-review.json`: passed with `applied_item_count=7` and `remaining_unresolved_authority_count=0`
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id v1-cg-ecid-source-delta-review --source-set-id source-set-8a4005c8a083af1a`: passed with `56` applicable authorities, `340` non-applicable authorities, and `0` unresolved decisions
- `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id v1-cg-ecid-source-delta-review --source-set-id source-set-8a4005c8a083af1a`: passed with `56` generated rules
- `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-source-delta-review`: failed closed as expected at `14/17`; remaining blockers are `compliance_gold_eval`, `compliance_review`, and `forest_plan_component_eval`

Residual risks:

- the replay is still `reviewer_ready=false`; the remaining blockers are no longer applicability
  adjudications, but replay-scoped compliance/gold-eval artifacts and East Crazies forest-plan
  component findings
- `phase-eval` still surfaces `compliance_gold_eval` as a replay blocker because the current gold
  eval remains bound to proving-lane source set `source-set-ba8d0feae79501b8`

Immediate next step if this slice is continued:

1. Repair the East Crazies forest-plan component gaps in
   `source_library/reviews/v1-cg-ecid-source-delta-review/forest_plan_component_eval_results.json`.
2. Regenerate replay-scoped `compliance_review` artifacts for
   `v1-cg-ecid-source-delta-review`.
3. Refresh replay-scoped compliance-gold evidence if `phase-eval` still blocks on
   `source_set_mismatch`, then rerun `phase-eval --review-id v1-cg-ecid-source-delta-review`.

## Replay Context Contract Hardening

The replay-context hardening milestone is now implemented for archived review lane
`v1-cg-ecid-source-delta-review`.

- tracked replay authority:
  `config/replay_contexts/v1-cg-ecid-source-delta-review.json` now binds the current replay to
  archived merged source set `source-set-8a4005c8a083af1a` and archived merged catalog gate
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/`
- new code surface:
  `src/usfs_r1_ea_sources/replay_context.py` now owns tracked replay-context loading, derives
  `source_catalog_path`, `source_set_manifest_path`, and `catalog_sqlite_path` from tracked
  `catalog_dir`, and rejects mismatched child-path echoes
- phase-eval hardening:
  `src/usfs_r1_ea_sources/evidence_graph.py` now auto-resolves tracked replay context from
  `review_id` (or the supplied review directory name), loads archived `source_set_id` and
  `catalog_dir` from tracked config, and fails closed on mismatched explicit `source_set_id` or
  `catalog_dir` overrides instead of silently falling back to the active catalog
- CLI/documentation alignment:
  `tests/test_cli.py`, `tests/test_evidence_graph.py`, `tests/test_replay_context.py`, `README.md`,
  `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/CGNF_CURRENT_REPLAY_REPAIR_MILESTONE_PLAN.md` now describe the tracked replay-context
  contract and review-identity auto-resolution path
- preserved non-goal boundary:
  no replay-specific forest-plan component eval contract was added; the proving-lane contract
  remains `config/forest_plan_component_eval_seed.json`
- live replay status after hardening:
  `phase-eval --review-id v1-cg-ecid-source-delta-review` now binds to the archived merged catalog
  gate, but the replay remains `reviewer_ready=false`; this milestone did not resolve the `7`
  applicability adjudications, the East Crazies forest-plan component repair lane, or replay
  compliance-review regeneration

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_evidence_graph.py tests/test_v1_ea_eval.py tests/test_replay_context.py tests/test_architecture_contract.py`: passed `74/74`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- replay-context negative proof:
  `PYTHONPATH=src python - <<'PY' ... run_phase_aligned_eval(output_dir=Path("source_library"), review_id="v1-cg-ecid-source-delta-review", catalog_dir=Path("source_library/catalog")) ... PY`
  raised `ReplayContextMismatchError`
- replay-context positive proof:
  `PYTHONPATH=src python - <<'PY' ... run_phase_aligned_eval(output_dir=Path("source_library"), review_id="v1-cg-ecid-source-delta-review") ... PY`
  returned `review_id=v1-cg-ecid-source-delta-review`,
  `source_set_id=source-set-8a4005c8a083af1a`, archived merged `catalog_dir`, and
  `reviewer_ready=False`
- proving-lane regression:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/forest_plan_component_eval_seed.json`
  passed `35/35`
- `git diff --check`: passed

Residual risks:

- the current replay is still blocked on the same content work: `7` applicability adjudications,
  forest-plan component-gap repair, and replay-scoped compliance-review regeneration
- tracked replay context is wired only into `phase-eval` in this milestone; any later replay
  commands that still need archived-path awareness should be reviewed explicitly rather than
  assumed safe by analogy

Immediate next step if this slice is continued:

1. Continue the current East Crazies replay repair lane: close the `7` applicability adjudications,
   repair the remaining forest-plan component gaps, regenerate replay-scoped `compliance-review`,
   then rerun review-scoped `phase-eval`.

## Region 1 Forest-Plan Stale-Surface Refresh

The Region 1 forest-plan stale surfaces are now resolved and committed truth is aligned to the live
active full-canonical source set `source-set-5e65d845ce77e1a0`.

- config alignment:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` now points at the `5e65...`
  `component_inventory_build_coverage.json`, promotes `custer-gallatin-nf`, `flathead-nf`,
  `helena-lewis-and-clark-nf`, `idaho-panhandle-nfs`, and `kootenai-nf`, and keeps
  `beaverhead-deerlodge-nf`, `bitterroot-nf`, `dakota-prairie-grasslands`, `lolo-nf`, and
  `nez-perce-clearwater-nfs` blocked on
  `plan_component_labels_not_detected` plus `plan_standard_labels_not_detected`
- promotion-suite alignment:
  `config/promotion_suite_v1.json` now pins `full_canonical_source_set_id` and all embedded
  full-canonical source-set checks to `source-set-5e65d845ce77e1a0`
- graph-contract alignment:
  `config/nepa_3d_graph_contract_v1.json` and
  `src/usfs_r1_ea_sources/nepa_3d_graph_contract.py` now recognize
  `plan_component_labels_not_detected` and `plan_standard_labels_not_detected` as valid readiness
  blocker types
- refreshed downstream truth:
  `nepa-knowledge-graph-export` on `source-set-5e65d845ce77e1a0` now passes with `66` checks,
  `0` failed, `2,132` nodes, `3,872` edges,
  `region1_forest_plan_graph_ready_profile_count=5`, and
  `region1_forest_plan_blocked_profile_count=5`
- refreshed promotion truth:
  `promotion-suite` now reports `current_promotion_ready=true`,
  `full_canonical_corpus_ready=true`, `promotion_ready=true`, `expansion_ready=false`, and
  `full_canonical_failure_category_counts={}`
- next real blocker boundary:
  stale-surface repair is complete; remaining work is parser/component recovery for the five blocked
  forests plus the separate expansion lane

Verification in this pass:

- `python -m json.tool config/region1_forest_plan_readiness_nepa_3d_v1.json`: passed
- `python -m json.tool config/promotion_suite_v1.json`: passed
- `PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py`: passed `29/29`
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`: passed with `full_canonical_corpus_ready=true`

## Region 1 Forest-Plan Active-Source-Set Refresh

The active full-canonical derived lane has now been refreshed onto the live catalog source set
`source-set-5e65d845ce77e1a0`.

- tracked build-contract alignment:
  `config/r1_forest_plan_component_inventory_build_manifest.json` now points
  `active_full_canonical` at `source-set-5e65d845ce77e1a0`
- refreshed extraction/currentness/inventory/graph lane:
  `reuse-inventory` reported `already_current_count=349`, `needs_extract_count=0`, and
  `excluded_count=1`; `extract-build --reuse-existing` rewrote `349/349` extracted rows and
  `75,745` chunks under `source-set-5e65d845ce77e1a0`
- refreshed full-canonical inventory result:
  `forest-plan-components-build --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json --source-set-id source-set-5e65d845ce77e1a0`
  now writes `668` components and `108` standards under
  `source_library/derived/source-set-5e65d845ce77e1a0/forest_plan_components/`
- passing forests on the refreshed active-source-set replay:
  `custer-gallatin-nf` (`329/58`), `flathead-nf` (`80/20`),
  `helena-lewis-and-clark-nf` (`257/28`), `idaho-panhandle-nfs` (`1/1`), and
  `kootenai-nf` (`1/1`)
- remaining typed blockers on the refreshed replay:
  `beaverhead-deerlodge-nf`, `bitterroot-nf`, `dakota-prairie-grasslands`, `lolo-nf`, and
  `nez-perce-clearwater-nfs`, all still failing on
  `plan_component_labels_not_detected` plus `plan_standard_labels_not_detected`
- refreshed downstream derived lane on the same source set:
  `authority-currentness` passed with `35` authority families and `207` source-currentness records;
  `retrieval-build` passed with `75,745` chunks and `reviewer_ready=true`;
  `evidence-graph-build` passed with `153,187` nodes and `533,938` edges;
  `claim-extract` passed with `101,856` claims;
  `rule-claim-link` passed with `211` links and `0` gaps;
  `nepa-knowledge-graph-export` passed with `66` checks, `0` failed checks, `2,128` nodes, and
  `3,825` edges
- durable-doc alignment in this pass:
  `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/R1_FOREST_PLAN_COMPONENT_INVENTORY_PROMOTION_MILESTONE_PLAN.md` now describe
  `source-set-5e65d845ce77e1a0` as both the live active catalog and the refreshed full-canonical
  derived lane
- remaining stale surfaces:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` still records only one validated
  inventory, and `promotion-suite` still points
  `full_canonical_source_set_id` at `source-set-34061d1e4bf6c460`, reporting
  `full_canonical_corpus_ready=false` with
  `full_canonical_failure_category_counts={"stale_artifact": 2}`

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_inventory_build_manifest.py tests/test_architecture_contract.py`: passed `13/13`
- `PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources extract-build --output-dir source_library --reuse-existing --reuse-inventory-path source_library/derived/source-set-5e65d845ce77e1a0/reuse_inventory/reuse_inventory.json`: passed with `349` extracted rows, `75,745` chunks, and `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`: stopped as intended with five typed blockers and summary `component_count=668`, `standard_count=108`, `coverage_passed=false`
- `PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `reviewer_ready=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`: passed as a command and reported stale full-canonical artifacts against `source-set-34061d1e4bf6c460`

Immediate next step if this slice is continued:

1. Promote the refreshed `source-set-5e65d845ce77e1a0` results into
   `config/region1_forest_plan_readiness_nepa_3d_v1.json` and repoint the full-canonical
   promotion-suite contract so the five validated forests and five typed blockers become the
   current promoted full-canonical truth.

## Region 1 Forest-Plan Inventory Re-Baseline

The Region 1 forest-plan component inventory promotion lane has now been re-baselined in durable
docs to the live active catalog source set.

- live active catalog source set:
  `source-set-5e65d845ce77e1a0` now resolves from `source_library/catalog/source_set_manifest.json`
- latest fully materialized full-canonical derived lane:
  `source-set-34061d1e4bf6c460` still owns the newest local `authority_currentness`,
  `forest_plan_components`, and `knowledge_graph` artifact families
- key correction:
  Sequence 4 is no longer a pure readiness-promotion step; it must first refresh the manifest-owned
  full-canonical derived lane onto `source-set-5e65d845ce77e1a0`, then promote readiness and graph
  truth from that refreshed replay
- durable-doc updates in this pass:
  `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/R1_FOREST_PLAN_COMPONENT_INVENTORY_PROMOTION_MILESTONE_PLAN.md` now state that the repo is
  split between a newer live catalog and an older fully materialized inventory/graph lane instead
  of describing `source-set-34061d1e4bf6c460` as the current active catalog
- explicit non-goal:
  this pass did not refresh `config/r1_forest_plan_component_inventory_build_manifest.json` or run
  a new active-source-set inventory/currentness/graph replay; it only corrected the milestone
  baseline and next-sequence routing

Verification in this pass:

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/R1_FOREST_PLAN_COMPONENT_INVENTORY_PROMOTION_MILESTONE_PLAN.md --strict`
- `git diff --check`

Residual risks:

- `config/r1_forest_plan_component_inventory_build_manifest.json` still points at
  `source-set-34061d1e4bf6c460`, so config/runtime truth is still split until the active-source-set
  refresh sequence lands
- the readiness config still records only one validated inventory and has not yet been promoted to
  reflect the three validated / seven blocked replay on the older full-canonical lane

Immediate next step if this slice is continued:

1. Refresh the tracked full-canonical build manifest and derived replay surfaces onto
   `source-set-5e65d845ce77e1a0`, then resume readiness and NEPA 3D graph promotion from that
   active-source-set replay.

## Region 1 Primary Plan Role Classification Milestone

The primary-plan role-classification milestone in
`docs/R1_FOREST_PLAN_PRIMARY_PLAN_ROLE_CLASSIFICATION_MILESTONE_PLAN.md` is now implemented in
code and focused tests.

- classifier change:
  `src/usfs_r1_ea_sources/catalog.py` now promotes only manifest-declared supplemental primary plan
  rows from `forest_plan_support` to `forest_plan`; ordinary register rows remain support-scoped
- tracked authority:
  the override is derived from
  `config/r1_forest_plan_component_inventory_build_manifest.json`, not a Python-only allowlist
- focused gates now pass:
  `tests/test_catalog.py`, `tests/test_forest_plan_source_delta_readiness.py`, and
  `tests/test_architecture_contract.py`
- live catalog replay proof:
  rebuilding `source_library/catalog/` from
  `corpus-update-2026-05-01-cg-support-batches` plus
  `r1-forest-plan-source-delta-capture-20260510-refresh-batches` under the current uncommitted
  worktree produced transient active catalog `source-set-5e65d845ce77e1a0`
- active catalog result:
  `R1PLAN-dakota-prairie-grasslands-03`, `R1PLAN-flathead-nf-02`, `R1PLAN-kootenai-nf-02`,
  `R1PLAN-lolo-nf-02`, and `R1PLAN-nez-perce-clearwater-nfs-06` now classify as
  `document_role=forest_plan`; negative control `R1PLAN-beaverhead-deerlodge-nf-03` remains
  `forest_plan_support`
- active chunk proof:
  `source_library/derived/source-set-5e65d845ce77e1a0/chunks/chunks.jsonl` now carries
  `document_role=forest_plan` chunks for all five promoted source IDs with chunk counts
  `2`, `899`, `336`, `580`, and `278` respectively
- isolated downstream proof:
  single-forest builds against the refreshed chunks now show `flathead-nf` building `80`
  components / `20` standards and `kootenai-nf` building `1` component / `1` standard; Dakota
  Prairie, Lolo, and Nez Perce-Clearwater now fail downstream of role classification rather than
  because the primary plan body is absent from `document_role=forest_plan`
- explicit non-goal boundary preserved:
  this milestone did not expand legacy parser support or promote a new active-source-set manifest
  reference

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_forest_plan_source_delta_readiness.py tests/test_architecture_contract.py`: passed `22/22`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --output-dir source_library --config config/downloader.toml --batch-run-id corpus-update-2026-05-01-cg-support-batches --batch-run-id r1-forest-plan-source-delta-capture-20260510-refresh-batches --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv`: passed with transient active catalog `source-set-5e65d845ce77e1a0`
- `PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`: passed with `reuse_extraction_count=349`
- `PYTHONPATH=src python -m usfs_r1_ea_sources extract-build --output-dir source_library --reuse-existing --reuse-inventory-path source_library/derived/source-set-5e65d845ce77e1a0/reuse_inventory/reuse_inventory.json`: passed with `349` extracted rows and `75,745` chunks
- isolated Python-driven single-forest inventory runs against `source-set-5e65d845ce77e1a0` refreshed chunks: passed for `flathead-nf` and `kootenai-nf`; produced downstream non-role blockers for Dakota Prairie, Lolo, and Nez Perce-Clearwater

Residual risks:

- the tracked manifest still pins active full-canonical build rows to committed source set
  `source-set-34061d1e4bf6c460`, so a manifest-batch replay against transient active catalog
  `source-set-5e65d845ce77e1a0` correctly stops on source-set-reference mismatch
- the next real blockers for these five forests are parser/plan-format issues, not catalog role
  classification

Immediate next step if this slice is continued:

1. Decide whether to refresh the tracked full-canonical source-set reference before broader
   promotion work, or keep the committed `source-set-34061d1e4bf6c460` contract and move directly
   into parser expansion for the newly visible primary plan bodies.

## Region 1 Forest-Plan Inventory Sequence 3

Sequence 3 of `docs/R1_FOREST_PLAN_COMPONENT_INVENTORY_PROMOTION_MILESTONE_PLAN.md` is now
implemented in the working tree. This slice materializes the active-source-set inventory artifacts,
stops the combined Region 1 build on typed blockers instead of borrowed inventory reuse, and proves
the active graph export can run against the owned inventory path.

- reuse-first extraction materialized the active chunk layer:
  `reuse-inventory` reported `349` reusable extraction rows, `0` new extraction requirements, and
  `1` excluded row; `extract-build --reuse-existing` then wrote `349/349` extracted rows and
  `75,745` chunks under `source-set-34061d1e4bf6c460`
- active inventory ownership closed:
  `forest-plan-components-build --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  now writes `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/`
- live build result:
  the active combined inventory contains `587` components and `87` standards; validated profiles
  are `custer-gallatin-nf` (`329/58`), `helena-lewis-and-clark-nf` (`257/28`), and
  `idaho-panhandle-nfs` (`1/1`)
- explicit typed blockers preserved:
  `beaverhead-deerlodge-nf`, `bitterroot-nf`, `dakota-prairie-grasslands`, `flathead-nf`,
  `kootenai-nf`, `lolo-nf`, and `nez-perce-clearwater-nfs` each stop on
  `plan_component_labels_not_detected` plus `plan_standard_labels_not_detected`
- aggregate coverage shape:
  the only failing build-coverage check is `all_profile_builds_pass`; there are no duplicate-ID,
  validation-error, or inventory-ownership failures left in the active build
- active graph replay is now green with the owned inventory path:
  `nepa-knowledge-graph-export` against `source-set-34061d1e4bf6c460` and
  `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/component_inventory.json`
  passed with `66` checks, `0` failed checks, `2,047` nodes, and `3,582` edges
- promotion-suite replay result:
  `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `full_canonical_failure_category_counts={}`, and `expansion_ready=false`

Verification in this pass:

- `PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory --output-dir source_library --source-set-id source-set-34061d1e4bf6c460`: passed with `reuse_extraction_count=349`, `needs_extract_count=0`, `excluded_count=1`
- `PYTHONPATH=src python -m usfs_r1_ea_sources extract-build --output-dir source_library --reuse-existing --reuse-inventory-path source_library/derived/source-set-34061d1e4bf6c460/reuse_inventory/reuse_inventory.json`: passed with `extracted_count=349`, `failed_count=0`, `chunk_count=75745`, `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-34061d1e4bf6c460 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`: stopped as intended with typed blockers and summary `component_count=587`, `standard_count=87`, `coverage_passed=false`
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-34061d1e4bf6c460 --authority-currentness-path source_library/derived/source-set-34061d1e4bf6c460/authority_currentness/authority_currentness_report.json --evidence-graph-nodes-path source_library/derived/source-set-8a4005c8a083af1a/evidence_graph/document_graph_nodes.jsonl --evidence-graph-edges-path source_library/derived/source-set-8a4005c8a083af1a/evidence_graph/document_graph_edges.jsonl --claims-path source_library/derived/source-set-8a4005c8a083af1a/claims/claims.jsonl --rule-claim-links-path source_library/derived/source-set-8a4005c8a083af1a/rule_claim_links/nepa-ea-v0/0.4.0/rule_claim_links.jsonl --forest-plan-components-path source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/component_inventory.json`: passed with `validation_passed=true`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`: passed with `full_canonical_corpus_ready=true`

Residual risks:

- `config/region1_forest_plan_readiness_nepa_3d_v1.json` still records only `custer-gallatin-nf`
  as `component_inventory_validation.status="validated"` and leaves the other nine profiles at
  `component_inventory_build_required`, so graph/readiness profile truth is the remaining stale
  surface rather than inventory ownership
- the seven blocked forests still need parser/profile promotion work before Region 1 inventory
  completeness can be described as broadly validated

Immediate next step if this slice is continued:

1. Implement Sequence 4 by promoting the active build results into
   `config/region1_forest_plan_readiness_nepa_3d_v1.json` and related graph/readiness summaries so
   the three validated inventories and seven typed blockers replace the current stale profile
   statuses without weakening `region1_completeness_claim=false`.

## Region 1 Forest-Plan Inventory Sequence 2

Sequence 2 of `docs/R1_FOREST_PLAN_COMPONENT_INVENTORY_PROMOTION_MILESTONE_PLAN.md` is now
implemented in code, tests, and durable alignment docs. This slice hardens the builder/runtime but
does not yet run the live active-source-set inventory build.

- builder runtime hardened:
  `forest-plan-components-build` now supports `--manifest-path` for tracked Region 1 batch builds
  while preserving the existing single-forest `--source-record-id` / `--plan-version` rebuild path
- canonical inventory contract preserved:
  manifest-driven builds still write one source-set inventory artifact family at
  `source_library/derived/<source_set_id>/forest_plan_components/` instead of switching consumers
  to ad hoc per-forest files
- aggregate coverage added:
  `component_inventory_build_coverage.json` now records `build_scope`, `source_record_ids`, and
  per-profile `profile_results` in addition to aggregate selected chunk, component, standard,
  duplicate-ID, validation-error, and quality-issue checks
- fail-closed collision proof added:
  regression coverage now proves a manifest-driven cross-profile duplicate component ID fails the
  aggregate build even when per-profile rows can each build in isolation
- resolver compatibility preserved:
  `load_forest_plan_component_inventory(..., forest_unit_id=...)` continues to filter the combined
  inventory safely for existing review lanes
- durable alignment closed:
  `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/OUTPUT_SCHEMAS.md`, and the milestone plan now
  route the next boundary to Sequence 3 instead of incorrectly describing the builder as
  single-forest-only or “next up”

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_forest_plan_resolver.py tests/test_architecture_contract.py`: passed `56/56`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/R1_FOREST_PLAN_COMPONENT_INVENTORY_PROMOTION_MILESTONE_PLAN.md --strict`: passed
- `git diff --check`: passed

Residual risks:

- this slice hardens the runtime contract but does not yet materialize
  `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/`
- the active full-canonical lane still fails ownership/readiness until the live Sequence 3 build is
  run and either passes or stops on typed profile blockers
- unrelated viewer code/test worktree edits remain present, so this sequence is aligned in working
  tree state but still not closed as a local atomic commit in this pass

Immediate next step if this slice is continued:

1. Implement Sequence 3 by running the manifest-driven builder for
   `source-set-34061d1e4bf6c460`, validating the resulting multi-forest inventory artifact family,
   and preserving explicit typed blockers for any forest that still cannot be promoted.

## Region 1 Forest-Plan Inventory Sequence 1

Sequence 1 of `docs/R1_FOREST_PLAN_COMPONENT_INVENTORY_PROMOTION_MILESTONE_PLAN.md` is now
implemented. This slice adds the tracked Region 1 build contract but does not change the
single-forest builder runtime yet.

- tracked build manifest added:
  `config/r1_forest_plan_component_inventory_build_manifest.json` now covers all `10` Region 1
  readiness profiles against active full-canonical source set `source-set-34061d1e4bf6c460`
- config-owned build inputs:
  each row records `plan_version`, `primary_plan_source_record_id`, grouped
  `build_source_record_ids_by_role`, and typed `promotion_eligibility`, including multipart Dakota
  Prairie plan inputs and the Nez Perce-Clearwater currentness-vs-primary-plan split
- validation contract added:
  `src/usfs_r1_ea_sources/forest_plan_inventory_build_manifest.py` now fails on unsupported
  source-set reference types, duplicate forest IDs, missing readiness-profile coverage, missing
  readiness source-record coverage, and rows whose declared primary-plan source ID is absent from
  their grouped build inputs
- regression coverage:
  `tests/test_forest_plan_inventory_build_manifest.py` locks the default all-10-profile manifest
  and the new fail-closed validation paths
- alignment recheck:
  current `source_library/catalog/source_set_manifest.json` still resolves to
  `source-set-34061d1e4bf6c460`, the manifest's `active_full_canonical` reference matches that
  live source set, and manifest roster coverage is `10/10` against
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_components.py tests/test_architecture_contract.py`: passed `34/34`
- `python -m json.tool config/forest_plan_profiles.json /tmp/forest_plan_profiles.validated.json`: passed
- `python -m json.tool config/r1_forest_plan_component_inventory_build_manifest.json /tmp/r1_inventory_build_manifest.validated.json`: passed
- `git diff --check`: passed

Residual risks:

- this milestone only closes the tracked config contract; `forest-plan-components-build` is still a
  single-forest command
- active full-canonical source set `source-set-34061d1e4bf6c460` still does not own a canonical
  multi-forest `forest_plan_components/` artifact family

Immediate next step if this slice is continued:

1. Implement Sequence 2 by teaching `forest-plan-components-build` to consume the tracked manifest
   and emit one canonical multi-forest inventory artifact family for the active full-canonical
   source set while preserving the current single-forest invocation path.

## Region 1 Forest-Plan Inventory Alignment Check

The post-Sequence-0 alignment replay is now closed. The new ownership gate is behaving correctly,
and the current gap is status/doc drift rather than missing enforcement.

- fresh active-source-set replay:
  rerunning `nepa-knowledge-graph-export` for `source-set-34061d1e4bf6c460` against the archived
  component inventory now fails exactly where Sequence 0 said it should
- live failure shape:
  `validation_passed=false`, `validation_check_count=66`,
  `failed_validation_check_count=1`, and
  `failure_category_counts={"graph_forest_plan_inventory_ownership_gap": 1}`
- concrete failing check:
  `nepa_3d_graph_forest_plan_inventory_owned_by_source_set` expects
  `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/component_inventory.json`
  with payload `source_set_id=source-set-34061d1e4bf6c460`, but the current replay still points at
  `source_library/derived/source-set-8a4005c8a083af1a/forest_plan_components/component_inventory.json`
  with payload `source_set_id=source-set-8a4005c8a083af1a`
- promotion-suite alignment:
  after refreshing the active graph artifact, `promotion-suite` now reports
  `current_promotion_ready=true`, `full_canonical_corpus_ready=false`, `promotion_ready=true`,
  `expansion_ready=false`, `passed_required_full_canonical_result_count=3`, and
  `full_canonical_failure_category_counts={"graph_viewer_export_invalid": 2}`
- affected full-canonical checks:
  `full_canonical_nepa_3d_source_set_graph_validation` and
  `full_canonical_nepa_3d_source_set_graph_summary` now fail closed as expected because the active
  source-set graph validation is no longer green

Verification in this pass:

- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-34061d1e4bf6c460 --authority-currentness-path source_library/derived/source-set-34061d1e4bf6c460/authority_currentness/authority_currentness_report.json --evidence-graph-nodes-path source_library/derived/source-set-8a4005c8a083af1a/evidence_graph/document_graph_nodes.jsonl --evidence-graph-edges-path source_library/derived/source-set-8a4005c8a083af1a/evidence_graph/document_graph_edges.jsonl --claims-path source_library/derived/source-set-8a4005c8a083af1a/claims/claims.jsonl --rule-claim-links-path source_library/derived/source-set-8a4005c8a083af1a/rule_claim_links/nepa-ea-v0/0.4.0/rule_claim_links.jsonl --forest-plan-components-path source_library/derived/source-set-8a4005c8a083af1a/forest_plan_components/component_inventory.json`: failed as expected with `graph_forest_plan_inventory_ownership_gap`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`: passed as a command and reported `full_canonical_corpus_ready=false`

Residual risks:

- the active full-canonical lane is now explicitly not promotion-ready until it owns a local
  component inventory artifact family
- top-level repo docs that claimed full-canonical green required alignment to this refreshed state

Immediate next step if this slice is continued:

1. Sequence 1 is now closed. The next implementation boundary is Sequence 2 multi-forest builder
   hardening.

## Region 1 Forest-Plan Component Inventory Promotion Sequence 0

Sequence 0 of `docs/R1_FOREST_PLAN_COMPONENT_INVENTORY_PROMOTION_MILESTONE_PLAN.md` is now
implemented as a gate-first baseline slice. This pass did not build multi-forest inventories yet.
It made the active-vs-archived inventory ownership gap executable and documented.

- live baseline confirmed from local artifacts:
  - active source set `source-set-34061d1e4bf6c460` does not own
    `source_library/derived/source-set-34061d1e4bf6c460/forest_plan_components/component_inventory.json`
  - archived source set `source-set-8a4005c8a083af1a` owns the only local
    `forest_plan_components/component_inventory.json`
  - readiness config still records `10` tracked Region 1 profiles, `1` validated inventory, and
    `9` `component_inventory_build_required` profiles
- implementation change:
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py` now adds
  `nepa_3d_graph_forest_plan_inventory_owned_by_source_set`, which fails closed when a
  `nepa-knowledge-graph-export` replay borrows another source set's
  `forest_plan_components/component_inventory.json` or payload `source_set_id`
- regression coverage:
  `tests/test_nepa_knowledge_graph_export.py` now proves the old promoted-profile inventory
  presence check can still pass while the new ownership gate fails on a borrowed inventory path
- plan review correction:
  Sequence 0 verification now includes `tests/test_architecture_contract.py` because this is a
  generated-artifact ownership boundary change, not only a fixture/test slice

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py`: passed `31/31`
- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/R1_FOREST_PLAN_COMPONENT_INVENTORY_PROMOTION_MILESTONE_PLAN.md --strict`: passed
- `git diff --check`: passed

Residual risks:

- the active full-canonical source set still lacks owned `forest_plan_components/` artifacts, so
  the new gate currently documents a real blocker rather than closing it
- the tracked multi-forest build contract now exists, but the builder runtime still cannot consume
  it to materialize an active-source-set-owned canonical inventory artifact family

Immediate next step if this slice is continued:

1. Sequence 1 is now closed. The next implementation boundary is Sequence 2 multi-forest builder
   hardening over the tracked manifest contract.

## Full Canonical Graph-Capability Gate

The full-canonical graph-capability milestone is now closed through operational artifact
materialization plus aligned docs. The default promotion manifest still requires the active
full-canonical source set to carry its own `authority_currentness` report plus NEPA 3D source-set
graph validation and summary artifacts, and the active lane now satisfies that stricter boundary
locally.

- manifest change: `config/promotion_suite_v1.json` now adds
  `full_canonical_authority_currentness`,
  `full_canonical_nepa_3d_source_set_graph_validation`, and
  `full_canonical_nepa_3d_source_set_graph_summary` as
  `required_for_full_canonical_corpus=true` results, all keyed to
  `derived/{full_canonical_source_set_id}/...`
- test coverage: `tests/test_promotion_suite.py` now locks the committed manifest shape for those
  full-canonical graph-capability artifacts and proves runtime path resolution with
  `{full_canonical_source_set_id}` placeholders
- operational closeout: `authority-currentness` now materializes
  `source_library/derived/source-set-34061d1e4bf6c460/authority_currentness/authority_currentness_report.json`
  with `validation_passed=true`, `35` authority families, `207` source-currentness records, and
  source partitions `active_review_corpus=349` plus `candidate_blocked_source=1`
- operational closeout: `nepa-knowledge-graph-export` now materializes
  `source_library/derived/source-set-34061d1e4bf6c460/knowledge_graph/nepa_3d_graph_validation.json`
  and `nepa_3d_graph_summary.json` with `validation_passed=true`, `65` checks, `0` failed checks,
  `1,789` nodes, `2,808` edges, and readiness blocker counts
  `forest_profile_not_ready=62`, `fsh_chapter_delta_required=2`, `missing_source=33`,
  `superseded_source=3`
- viewer default behavior: `viewer/nepa-3d/` now opens on the full validated knowledge base for
  the resolved source set, keeping laws, regulations, policies, forest plans, and supporting
  documents in the default scene while review-specific and single-example views remain optional
  scene or selector choices
- historical replay status before the Sequence 0 ownership-gate refresh:
  rerunning `promotion-suite` against the current local `source_library/` reported
  `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `promotion_ready=true`, `expansion_ready=false`, and
  `passed_required_full_canonical_result_count=5/5`. This is superseded by the alignment check
  above.

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py`: passed `19/19`
- `PYTHONPATH=src python -m usfs_r1_ea_sources authority-currentness --output-dir source_library --source-set-id source-set-34061d1e4bf6c460`: passed with `validation_passed=true`, `35` authority families, `207` source-currentness records, and source partitions `active_review_corpus=349` plus `candidate_blocked_source=1`
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-34061d1e4bf6c460 --authority-currentness-path source_library/derived/source-set-34061d1e4bf6c460/authority_currentness/authority_currentness_report.json --evidence-graph-nodes-path source_library/derived/source-set-8a4005c8a083af1a/evidence_graph/document_graph_nodes.jsonl --evidence-graph-edges-path source_library/derived/source-set-8a4005c8a083af1a/evidence_graph/document_graph_edges.jsonl --claims-path source_library/derived/source-set-8a4005c8a083af1a/claims/claims.jsonl --rule-claim-links-path source_library/derived/source-set-8a4005c8a083af1a/rule_claim_links/nepa-ea-v0/0.4.0/rule_claim_links.jsonl --forest-plan-components-path source_library/derived/source-set-8a4005c8a083af1a/forest_plan_components/component_inventory.json`: this historical pre-refresh pass recorded `validation_passed=true`, `65` checks, `0` failed checks, `1,789` nodes, and `2,808` edges; it is superseded by the failing ownership-gate replay above
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`: this historical pre-refresh pass reported `current_promotion_ready=true`, `full_canonical_corpus_ready=true`, `promotion_ready=true`, `expansion_ready=false`, `passed_required_full_canonical_result_count=5/5`, and `full_canonical_failure_category_counts={}`; it is superseded by the alignment replay above
- headless local browser smoke via Chrome channel + Playwright against `http://127.0.0.1:8765/viewer/nepa-3d/`: passed with resolved dataset `source-set-34061d1e4bf6c460`, `1,789/2,808` rendered at load, and validation text pointing to `source_library/derived/source-set-34061d1e4bf6c460/knowledge_graph/nepa_3d_graph.json`

Residual risks:

- the stronger full-canonical gate was green only on the pre-refresh artifact set; the current
  aligned state above blocks full-canonical readiness on inventory ownership while reviewer-facing
  promotion remains intentionally pinned to `source-set-ba8d0feae79501b8`
- merged-corpus East Crazies review replay on `source-set-8a4005c8a083af1a` is still blocked by
  `7` applicability adjudications and failing forest-plan component evaluation

Immediate next step if this slice is continued:

1. Keep reviewer-facing promotion pinned to `source-set-ba8d0feae79501b8` until the merged-corpus
   East Crazies replay becomes reviewer-ready.
2. Close the `7` applicability adjudications in
   `source_library/reviews/v1-cg-ecid-source-delta-review/applicability/`.
3. Close the remaining East Crazies forest-plan component gaps for the merged-corpus replay.

## NEPA 3D Readiness Blocker Clarity

The NEPA 3D blocker-clarity follow-on is now implemented and locally closed through code, tests,
refreshed graph artifacts, and browser smoke.

- contract/exporter change: `readiness_semantic_class` is now a required node/edge field in
  `config/nepa_3d_graph_contract_v1.json` and
  `src/usfs_r1_ea_sources/nepa_3d_graph_contract.py`
- exporter behavior: fresh graph exports classify red items as `synthetic_blocker_node`,
  `blocked_domain_node`, `blocker_relationship_edge`, or `blocked_relationship_edge` instead of
  relying on `display_status="readiness_blocked"` alone
- viewer behavior: `viewer/nepa-3d/app.js` now uses that field for legend, tooltip, detail,
  filter, and red edge/node styling, with heuristic fallback for older graph exports
- fixture/test coverage: smallest source-set/review graph fixtures now fail closed when those red
  semantics collapse together again
- live archived export refresh: rerunning `nepa-knowledge-graph-export` against the archived merged
  catalog gate for `source-set-8a4005c8a083af1a` now writes a graph with `validation_passed=true`,
  `65` checks, `0` failed checks, `1,789` nodes, `2,808` edges, `350` catalog source records,
  source partitions `active_review_corpus=349` plus `candidate_blocked_source=1`, and readiness
  blocker counts `forest_profile_not_ready=62`, `fsh_chapter_delta_required=2`,
  `missing_source=33`, `superseded_source=3`
- local browser smoke: served `viewer/nepa-3d/` on `http://127.0.0.1:8765/viewer/nepa-3d/`,
  verified the refreshed source set resolved at load, verified the legend and status/readiness
  filter taxonomy, and verified the detail rail for a blocked forest-plan node
  (`Blocked domain node`) plus an explicit `HAS_READINESS_BLOCKER` edge (`Explicit blocker edge`)
  against live DOM output

Verification in this pass:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_graph_contract.py`: passed `8/8`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_knowledge_graph_export.py`: passed `4/4`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_viewer.py`: passed `5/5`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py`: passed `5/5`
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-8a4005c8a083af1a --catalog-path source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/source_catalog.jsonl --catalog-graph-nodes-path source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/source_graph_nodes.jsonl --catalog-graph-edges-path source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/source_graph_edges.jsonl --source-set-manifest-path source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/source_set_manifest.json`: passed with `validation_passed=true`, `65` checks, `0` failed checks, `1,789` nodes, and `2,808` edges
- headless local browser smoke via Chrome channel + Playwright against `http://127.0.0.1:8765/viewer/nepa-3d/`: passed with resolved dataset `source-set-8a4005c8a083af1a`, `1,789/2,808` rendered at load, blocked-domain-node detail text present for `forest_plan:beaverhead-deerlodge-nf:R1PLAN-beaverhead-deerlodge-nf-02`, and explicit-blocker-edge detail text present for `edge:09a097081a624c08dfc9b85d`
- `git diff --check`: passed

Residual risks:

- the active promoted catalog source set `source-set-34061d1e4bf6c460` still lacks the
  authority-currentness artifact path the exporter expects, so the blocker-clarity live refresh was
  verified against the freshest archived merged gate (`source-set-8a4005c8a083af1a`) rather than
  the active catalog source set
- review-overlay graph artifacts were not regenerated in this pass; the live smoke covered the
  source-set graph path only

Immediate next step if this slice is continued:

1. If the active full canonical catalog needs to become the viewer default without fallback,
   generate the missing currentness-derived inputs under `source-set-34061d1e4bf6c460` and rerun
   the source-set NEPA 3D export there.
2. If reviewer workflows need the same red-taxonomy proof on review overlays, rerun the
   review-scoped export and smoke one live review overlay detail case.
3. Otherwise, the next milestone boundary is blocker reduction, not blocker-clarity semantics.

## Latest Full Canonical Corpus Promotion

The active `source_library/catalog/` contract has now been promoted to the full merged corpus under
the current code while keeping reviewer-ready East Crazies promotion explicit and separate.

- active full canonical catalog source set: `source-set-34061d1e4bf6c460`
- active catalog inputs:
  `corpus-update-2026-05-01-cg-support-batches` plus
  `r1-forest-plan-source-delta-capture-20260510-refresh-batches`
- active catalog counts: `350` source rows, `319` artifacts, `332` unique URLs,
  `349` `active_review_corpus` rows, `1` `candidate_blocked_source` row, and `160`
  supplemental source-delta rows
- preserved explicit gap: `R1PLAN-kootenai-nf-18` remains visible through
  `source_delta_input.skipped_gap_source_record_ids` and
  `config/r1_forest_plan_official_source_gap_evidence.json`
- current-promotion lane remains pinned to reviewer-ready source set
  `source-set-ba8d0feae79501b8`
- historical promotion-suite closeout before the Sequence 0 alignment replay reported:
  `current_promotion_ready=true`,
  `full_canonical_corpus_ready=true`,
  `promotion_ready=true`,
  `expansion_ready=false`

That earlier full-canonical gate state was satisfied locally for
`source-set-34061d1e4bf6c460`: the active `authority_currentness` artifact passes with `35`
authority families and `207` source-currentness records, the pre-refresh active NEPA 3D
source-set export passed with `65` checks, `0` failed checks, `1,789` nodes, and `2,808` edges,
and the local viewer resolved that active dataset directly without fallback. The alignment replay
above supersedes this state.

Important boundary:

- archived merged source set `source-set-8a4005c8a083af1a` remains the freshest fully replayed
  merged extraction/retrieval/graph surface
- active full canonical catalog source set `source-set-34061d1e4bf6c460` is the current code's
  promoted catalog truth
- merged-corpus East Crazies replay on `source-set-8a4005c8a083af1a` is still blocked by
  `7` applicability adjudications and failing forest-plan component evaluation, so full-corpus
  promotion does not mean reviewer-ready merged review promotion

Verification replay for plan alignment:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_captured_library.py`:
  passed `19/19`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_source_delta_readiness.py tests/test_cli.py`:
  passed `41/41`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py tests/test_final_qa_certification.py`:
  passed `30/30`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py`:
  passed `5/5`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`: passed
- `PYTHONPATH=src python -m compileall src`: passed
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-source-delta-readiness --output-dir source_library --source-delta-batch-run-id r1-forest-plan-source-delta-capture-20260510-refresh-batches --official-source-gap-evidence config/r1_forest_plan_official_source_gap_evidence.json`:
  passed with `failed_check_count=0`, `canonical_catalog_source_set_id=source-set-34061d1e4bf6c460`,
  and preserved gap `R1PLAN-kootenai-nf-18`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`:
  this historical pre-refresh run passed with `current_promotion_ready=true`,
  `full_canonical_corpus_ready=true`, `promotion_ready=true`, `expansion_ready=false`; the current
  aligned state is `full_canonical_corpus_ready=false` per the alignment check above
- `PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification --output-dir source_library --review-id v1-cg-ecid-compliance-review --validate-only`:
  passed `196/196` with `output_written=false`

Closeout implementation commit: `5aa32d9`

Residual risks:

- merged-corpus East Crazies replay on `source-set-8a4005c8a083af1a` still has `7` applicability
  adjudications and failing forest-plan component evaluation
- `R1PLAN-kootenai-nf-18` remains an accepted official-source gap, not a resolved download
- reviewer-facing promotion artifacts remain intentionally pinned to `source-set-ba8d0feae79501b8`
  until the merged review replay becomes reviewer-ready

Next milestone routing:

1. Close the `7` applicability adjudications in
   `source_library/reviews/v1-cg-ecid-source-delta-review/applicability/`.
2. Close the remaining East Crazies forest-plan component gaps for the merged-corpus replay.
3. After those are green, update reviewer-facing promotion and final-QA lanes to the merged
   full-corpus lane if the replay proves reviewer-ready.

## Latest Source-Delta Refresh

The 2026-05-10 refresh closes the remaining source-delta corpus gaps and moves the remaining work
fully into downstream review closure.

- register state: `160` source-delta rows and `1` preserved official-source gap after promoting
  `R1PLAN-nez-perce-clearwater-nfs-18` to the official project-record page
- refreshed capture run:
  `r1-forest-plan-source-delta-capture-20260510-refresh-batches`
- refreshed scoped source set: `source-set-bfe49a94e22fd1e2`
- refreshed merged source set: `source-set-8a4005c8a083af1a`
- merged extraction replay with external Docling OCR now validates with `349/349` required rows
  extracted, `0` failed rows, and `75,745` chunks
- merged source-set replay is fully green:
  `retrieval-eval` `12/12`, evidence graph `153,198` nodes / `533,949` edges, claim extraction
  `101,856` claims, rule-claim binding `211` links / `0` gaps, NEPA 3D source-set graph
  `1,789` nodes / `2,808` edges, and source-set `phase-eval` `7/7` with `reviewer_ready=true`
- readiness gate now reports `160` source-delta rows, `0` extraction blockers, retrieval `ready`,
  and one preserved official-source gap (`R1PLAN-kootenai-nf-18`)
- `applicability-authority-universe` now accepts `--catalog-path` and
  `--source-set-manifest-path` so archived merged catalogs can be used for noncanonical review
  replays without replacing `source_library/catalog/`

Merged-corpus review replay is now explicit under
`source_library/reviews/v1-cg-ecid-source-delta-review/` for the East Crazies package on
`source-set-8a4005c8a083af1a`. The replay is blocked, but the blockers are now concrete:

- applicability-first lane:
  `49` applicable authorities, `340` non-applicable authorities, `7` `needs_adjudication`
  authority-family template candidates, and adjudication template/worklist written under
  `source_library/reviews/v1-cg-ecid-source-delta-review/applicability/`
- forest-plan lane:
  resolver context validates, but component findings still report `6` gaps and component eval fails
  `9/35` seed cases
- review-scoped phase gate:
  `phase-eval --review-id v1-cg-ecid-source-delta-review --source-set-id source-set-8a4005c8a083af1a`
  now reports `12/17` phases passing with `reviewer_ready=false`

Immediate next work from this handoff:

1. Resolve the `7` applicability adjudications in
   `source_library/reviews/v1-cg-ecid-source-delta-review/applicability/applicability_adjudication_template.json`
   and rerun `applicability-adjudication-eval`, `applicability-adjudication-apply`,
   `applicability-validate`, and `applicability-generate-rule-pack`.
2. Resolve the remaining East Crazies forest-plan component gaps shown in
   `source_library/reviews/v1-cg-ecid-source-delta-review/forest_plan_component_findings.json` and
   `forest_plan_component_eval_results.json`.
3. Once applicability and component-eval are green, rerun `compliance-review`,
   `phase-eval --review-id v1-cg-ecid-source-delta-review --source-set-id source-set-8a4005c8a083af1a`,
   and any desired reviewer-facing artifacts.

## Region 1 Forest-Plan Document Register Promotion

The Region 1 forest-plan support-document register is now promoted into the controlled capture
pipeline as an explicit source-delta input. Use:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources dry-run --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --output-dir source_library --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-only
PYTHONPATH=src python -m usfs_r1_ea_sources preflight --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --output-dir source_library --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-only
PYTHONPATH=src python -m usfs_r1_ea_sources batch-download --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --output-dir source_library --run-id-prefix r1-forest-plan-source-delta-capture --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-only --batch-size 5 --plan-only
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --output-dir source_library --batch-run-id r1-forest-plan-source-delta-capture-20260510-batches --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-only
```

Promotion behavior is intentionally narrow:

- `source_delta_required` rows emit supplemental `WorkbookSource` records.
- `catalog_confirmed` rows are counted but are not re-emitted because they already exist in the
  workbook/catalog contract.
- `official_source_gap_documented` rows are counted as skipped gaps and are not corpus-ready.

Promotion acceptance is documented in
`docs/R1_FOREST_PLAN_DOCUMENT_REGISTER_PROMOTION_REPORT.md`. The real dry-run
`r1-forest-plan-promotion-dry-run-20260510` planned all `159` source-delta rows with no duplicates.
The scoped live preflight `r1-forest-plan-promotion-preflight-20260510` returned `158`
`preflight_ok` rows and one transient Forest Service `429` for
`R1PLAN-dakota-prairie-grasslands-19`; targeted retry
`r1-forest-plan-promotion-preflight-retry-dpg19-20260510` passed `1/1`.

Gap-closure update: `batch-download` now accepts the same Region 1 register source-delta contract.
Plan-only smoke run `r1-forest-plan-source-delta-capture-plan-20260510-batches` planned all `159`
source-delta rows in `33` batches: `139` `www.fs.usda.gov`, `18` `usfs-public.app.box.com`, and
`2` `federalregister.gov`.

Capture execution update: live batch run
`r1-forest-plan-source-delta-capture-20260510-batches` passed `33/33` child batches for all `159`
source-delta rows, with `158` unique artifacts and an empty repair queue. `catalog-build` now
accepts the same register source-delta contract. The scoped catalog gate built
`source-set-411b3736b3691eed` with `159` `forest_plan_support` rows, `158` artifacts,
`downloaded=158`, `duplicate_content=1`, and `catalog_validation.json` passing. That scoped catalog
snapshot is archived under
`source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/catalog_gate/`.

This older sequence snapshot is superseded by the full canonical promotion at the top of this
handoff. The active `source_library/catalog/` view is now full canonical source set
`source-set-34061d1e4bf6c460`, while the promoted downstream V1 derived artifacts remain pinned to
reviewer-ready source set `source-set-ba8d0feae79501b8`.

Source-delta readiness update: `forest-plan-source-delta-readiness` now builds the source-delta
report/gate over the promoted register, refresh batch capture, archived scoped catalog gate,
active full canonical catalog, tracked official-source gap evidence, and the live merged
extraction/retrieval surfaces. The live gate passes with `0` failed checks, schema
`r1-forest-plan-source-delta-readiness-v3`, scoped source set `source-set-bfe49a94e22fd1e2`,
canonical catalog source set `source-set-34061d1e4bf6c460`, `160` captured source-delta rows, and
official-source gap `R1PLAN-kootenai-nf-18` validated against
`config/r1_forest_plan_official_source_gap_evidence.json`. Generated JSON/Markdown reports are
ignored under
`source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/source_delta_readiness/`.

Sequence 3 merged catalog contract update: `catalog-build` now accepts repeated `--batch-run-id`
values plus `--catalog-dir` for archived gates. The freshest fully replayed merged gate is
archived at
`source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/`
as `source-set-8a4005c8a083af1a`. It combines canonical batch run
`corpus-update-2026-05-01-cg-support-batches` with refresh batch run
`r1-forest-plan-source-delta-capture-20260510-refresh-batches`, validates `350` source rows,
`319` artifacts, `332` unique URLs, `349` `active_review_corpus` rows, `1`
`candidate_blocked_source` row, `160` supplemental source-delta rows, and the preserved explicit
gap carried outside the downloaded catalog rows. The active `source_library/catalog/` view is now
promoted full canonical source set `source-set-34061d1e4bf6c460`.

Sequence 4 extraction/parser readiness update: the merged reuse inventory on
`source-set-7e2652d23e764068` classified `reuse_extraction=189`, `needs_extract=159`, and
`excluded=1`. `extract-build --catalog-dir ... --reuse-existing --reuse-inventory-path ...` ran
against the archived merged gate without touching `source_library/catalog`, reused `189` prior
rows, and after the fallback replay now extracts `341/349` merged-corpus rows with `7` explicit
`parser_error` rows. For the `159` support-document source-delta rows specifically, extraction
readiness is now `ready_with_blockers` with `152` extracted rows, `7` explicit parser blockers,
and complete source-record coverage.

Sequence 4 runtime-gap update after that artifact: `extract-build` now falls back to
`pypdf_text_fallback` when Docling is unavailable, and alternate-interpreter Docling is opt-in
through `USFS_R1_DOCLING_PYTHON` instead of being assumed implicitly. Targeted live smoke on merged
catalog PDFs `R1PLAN-beaverhead-deerlodge-nf-02`, `-03`, and `-04` now succeeds with
`parser_name=pypdf_text_fallback` and `fallback_error_class=docling_unavailable`.

Sequence 5 retrieval readiness update: `retrieval-build` now accepts `--catalog-dir` so the
archived merged catalog can supply review topics without replacing `source_library/catalog`.
`retrieval-eval` now supports `expect_no_hits: true` cases, and the tracked Region 1 source-delta
suite is `config/r1_forest_plan_source_delta_retrieval_eval.json`. Live retrieval validation now
passes on `source-set-7e2652d23e764068` with
`--allow-failed-extraction --allow-partial-extraction`, the `12`-case source-delta eval passes,
and the refreshed readiness gate reports retrieval `ready_with_blockers` with `152/152` extracted
support-document rows indexed and the same `7` upstream parser blockers preserved explicitly.
Alignment closeout for this milestone: extracted chunks now carry register-backed
`support_document_role` values for matching `R1PLAN-*` rows, including catalog-confirmed rows such
as `R1PLAN-custer-gallatin-nf-06`, so the current `12/12` eval pass is based on actual role-aware
filters rather than source-ID-targeted shortcuts. Current upstream parser blockers remain:
`R1PLAN-beaverhead-deerlodge-nf-08`, `R1PLAN-bitterroot-nf-07`,
`R1PLAN-dakota-prairie-grasslands-25`, `R1PLAN-idaho-panhandle-nfs-09`,
`R1PLAN-idaho-panhandle-nfs-10`, `R1PLAN-kootenai-nf-08`, and `R1PLAN-lolo-nf-12`.

Sequence 6 forest-profile readiness update: the same readiness report now emits concrete
`forest_profile_readiness` rows instead of placeholders. The live replay now keeps configured
profiles aligned with `config/forest_plan_profiles.json`: `custer-gallatin-nf` is the only ready
configured profile and `beaverhead-deerlodge-nf` is the only blocked configured profile. The
retrieval-ready register-only tracking rows are reported separately:
`flathead-nf`, `helena-lewis-and-clark-nf`, and `region-1-northern-region`. The remaining blocked
rows still carry source-ID-level blockers:
`R1PLAN-beaverhead-deerlodge-nf-08`, `R1PLAN-bitterroot-nf-07`,
`R1PLAN-dakota-prairie-grasslands-25`, `R1PLAN-idaho-panhandle-nfs-09`,
`R1PLAN-idaho-panhandle-nfs-10`, `R1PLAN-kootenai-nf-08`, `R1PLAN-kootenai-nf-18`,
`R1PLAN-lolo-nf-12`, and `R1PLAN-nez-perce-clearwater-nfs-18`. Custer Gallatin stays ready under
the current proving assumptions with `7/7` required support-document roles retrieval-ready.

Latest Sequence 6 alignment verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_source_delta_readiness.py`
  passed `7`.
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-source-delta-readiness --output-dir source_library --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-batch-run-id r1-forest-plan-source-delta-capture-20260510-batches --merged-catalog-gate-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate --extraction-source-set-id source-set-7e2652d23e764068 --reuse-inventory-path source_library/derived/source-set-7e2652d23e764068/reuse_inventory/reuse_inventory.json --official-source-gap-evidence config/r1_forest_plan_official_source_gap_evidence.json`
  passed with schema `r1-forest-plan-source-delta-readiness-v3`, configured profile readiness
  `1` ready / `1` blocked, and tracking-only readiness separated from configured-profile counts.

Sequence 7 corpus incorporation and downstream replay is complete for merged support-document
source set `source-set-7e2652d23e764068`. The downstream source-set-aware replay surfaces are now
fresh without stale-source-set confusion, and the remaining blockers are the explicit parser
failures plus the two official-source gaps.
The Sequence 7 alignment closeout confirmed that this remaining work is runtime-only; the durable
schema docs now also distinguish default reviewer-ready claim inputs from the explicit
`--allow-partial-claims` blocker-aware replay path.

Milestone plan:
`docs/R1_FOREST_PLAN_SOURCE_DELTA_READINESS_MILESTONE_PLAN.md`.

Latest Sequence 7 verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_nepa_3d_graph_contract.py tests/test_claim_extraction.py tests/test_rule_claim_binding.py tests/test_evidence_graph.py tests/test_nepa_knowledge_graph_export.py tests/test_cli.py tests/test_authority_currentness.py`
  passed `77`.
- `PYTHONPATH=src uv run --extra dev pytest` passed `517`.
- `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py` passed `5`.
- `PYTHONPATH=src uv run --extra dev ruff check src tests`, `PYTHONPATH=src python -m compileall src`,
  and `git diff --check` passed.
- `PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id source-set-7e2652d23e764068 --catalog-sqlite-path source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate/review_sources.sqlite --allow-partial-retrieval`
  passed with `validation_passed=true`, `reviewer_ready=false`, and `101,824` claims.
- `PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build --output-dir source_library --source-set-id source-set-7e2652d23e764068 --catalog-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate --allow-partial-retrieval`
  passed with `validation_passed=true`, `reviewer_ready=false`, `178,912` nodes, and `559,467`
  edges.
- `PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link --output-dir source_library --source-set-id source-set-7e2652d23e764068 --allow-partial-claims`
  passed with `validation_passed=true`, `reviewer_ready=false`, `211` links, and `0` gaps.
- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-7e2652d23e764068 --catalog-path source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate/source_catalog.jsonl --catalog-graph-nodes-path source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate/source_graph_nodes.jsonl --catalog-graph-edges-path source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate/source_graph_edges.jsonl --source-set-manifest-path source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate/source_set_manifest.json --region1-forest-plan-readiness source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/source_delta_readiness/r1_forest_plan_source_delta_readiness_report.json`
  passed with `validation_passed=true`, `1,837` nodes, `2,842` edges, and readiness blockers
  including `extraction_blocked` plus `official_source_gap`.
- `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id source-set-7e2652d23e764068 --catalog-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate`
  wrote a fresh source-set replay with `phase_count=7`, `passed_phase_count=6`,
  `reviewer_ready_phase_count=2`, `reviewer_ready=false`, and no stale `compliance_gold_eval`
  source-set mismatch phase.

Next work from this point: resolve the seven parser-blocked support-document rows, resolve the two
official-source gaps, or explicitly ask for a review replay against the merged corpus. No additional
Sequence 7 source-set alignment work is pending.

Latest Sequence 1 verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_source_delta_readiness.py tests/test_r1_forest_plan_document_register.py tests/test_cli.py`
  passed `32`.
- `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/forest_plan_source_delta_readiness.py src/usfs_r1_ea_sources/cli_derived.py tests/test_forest_plan_source_delta_readiness.py tests/test_r1_forest_plan_document_register.py tests/test_cli.py`
  passed.
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-source-delta-readiness --output-dir source_library --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-batch-run-id r1-forest-plan-source-delta-capture-20260510-batches --official-source-gap-evidence config/r1_forest_plan_official_source_gap_evidence.json`
  passed with `0` failed checks.

Latest Sequence 3 alignment verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_cli.py` passed `33`.
- `PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_captured_library.py tests/test_cli.py tests/test_architecture_contract.py`
  passed `44`.
- `PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --output-dir source_library --batch-run-id corpus-update-2026-05-01-cg-support-batches --batch-run-id r1-forest-plan-source-delta-capture-20260510-batches --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --catalog-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate`
  passed and produced `source-set-7e2652d23e764068` with `17` validation checks.
- `PYTHONPATH=src uv run --extra dev pytest` passed `490`.
- `PYTHONPATH=src uv run --extra dev ruff check src tests`, `PYTHONPATH=src python -m compileall src`,
  milestone plan lint, and `git diff --check` passed.

Latest Sequence 4 verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py tests/test_extract.py tests/test_reuse_inventory.py tests/test_forest_plan_source_delta_readiness.py` passed `50`.
- `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py` passed `5`.
- `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/extract.py src/usfs_r1_ea_sources/reuse_inventory.py src/usfs_r1_ea_sources/forest_plan_source_delta_readiness.py src/usfs_r1_ea_sources/cli_derived.py tests/test_cli.py tests/test_extract.py tests/test_reuse_inventory.py tests/test_forest_plan_source_delta_readiness.py` passed.
- `PYTHONPATH=src python -m compileall src` and `git diff --check` passed.
- `PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory --output-dir source_library --source-set-id source-set-7e2652d23e764068 --catalog-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate` passed with `reuse_extraction=189`, `needs_extract=159`, `excluded=1`.
- `PYTHONPATH=src python -m usfs_r1_ea_sources extract-build --output-dir source_library --catalog-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate --reuse-existing --reuse-inventory-path source_library/derived/source-set-7e2652d23e764068/reuse_inventory/reuse_inventory.json` completed with `341` extracted rows, `7` explicit `parser_error` rows, `1` excluded row, and `validation_passed=false` because the remaining blockers are real parser failures rather than hidden omissions.
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-source-delta-readiness --output-dir source_library --r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-batch-run-id r1-forest-plan-source-delta-capture-20260510-batches --merged-catalog-gate-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate --extraction-source-set-id source-set-7e2652d23e764068 --reuse-inventory-path source_library/derived/source-set-7e2652d23e764068/reuse_inventory/reuse_inventory.json --official-source-gap-evidence config/r1_forest_plan_official_source_gap_evidence.json` passed with schema `r1-forest-plan-source-delta-readiness-v2`, extraction `ready_with_blockers`, retrieval `ready_with_blockers`, `152` extracted support-document rows, and `7` explicit support-document parser blockers.
- `PYTHONPATH=src uv run --extra dev pytest tests/test_extract.py tests/test_cli.py tests/test_forest_plan_source_delta_readiness.py tests/test_reuse_inventory.py` passed `52`.
- `PYTHONPATH=src python - <<'PY' ... _extract_pdf(...) ... PY` smoke over merged-catalog PDFs `R1PLAN-beaverhead-deerlodge-nf-02`, `-03`, and `-04` succeeded with `parser_name=pypdf_text_fallback`, `fallback_error_class=docling_unavailable`, and large extracted text payloads (`942,552`, `3,878,548`, and `137,467` chars respectively).

Latest Sequence 5 verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_retrieval.py tests/test_forest_plan_source_delta_readiness.py tests/test_cli.py` passed `42`.
- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py` passed `27`.
- `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-7e2652d23e764068 --catalog-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate --allow-failed-extraction --allow-partial-extraction` passed with `validation_passed=true`, `reviewer_ready=false`, and `75,708` indexed chunks across `341` extracted sources.
- `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval --output-dir source_library --source-set-id source-set-7e2652d23e764068 --eval-file config/r1_forest_plan_source_delta_retrieval_eval.json` passed `12/12`.

## Region 1 Forest-Plan Document Register Hardening

`config/r1_forest_plan_document_register_draft.csv` is now an ingest-ready draft register for
Region 1 forest-plan support documents, subject to the explicit official-source gaps below. The
register has `189` rows: `28` already catalog-confirmed rows, `159` source-delta rows, and `2`
documented official-source gaps. No rows remain in the prior placeholder statuses
`needs_direct_link_resolution`, `needs_child_document_expansion`, or
`missing_official_source_research`.

The hardening slice resolved Flathead public reading-room Box files to stable official file-share
rows, expanded Dakota Prairie Appendices A-N, expanded Idaho Panhandle 2015 Biological Opinion
chapters, resolved Kootenai Biological Opinion chapters 1-4 from current official Forest Service
media links, resolved the Bitterroot grizzly-bear re-consultation BA/BO from the official Forest
Service Pinyon Public project record, and corrected Nez Perce-Clearwater Federal Register coverage.
Downloader support includes `box_public_file_download`, which keeps stable Box share URLs in the
register/workbook while resolving temporary BoxCloud PDF URLs at fetch time. Downloader support also
accepts ZIP artifacts for official support-document packages such as Lolo appendices.

Remaining register gaps are explicit:

- `R1PLAN-kootenai-nf-18`: 2026-05-10 official-source check found current Kootenai official
  planning/supporting pages with BO chapters 1-4, but no current official plan-level BA PDF.
- `R1PLAN-nez-perce-clearwater-nfs-18`: current Nez Perce-Clearwater official 2025 LMP page links
  a Box plan revision project record URL, but live access returned 404; the row points to the
  official planning page and tracked gap evidence until a replacement official project-record URL is
  acquired.

Verification for this slice:

- Custom CSV structural validation passed: `189` rows, `0` duplicate IDs, `0` unresolved
  placeholder statuses, valid HTTP(S) links, and documented gap IDs `R1PLAN-kootenai-nf-18` and
  `R1PLAN-nez-perce-clearwater-nfs-18`.
- Live Flathead Box preflight smoke passed for `R1PLAN-flathead-nf-02`: `preflight_ok`, HTTP
  `206`, `application/pdf`, adapter `box_public_file_download`.
- Live Bitterroot Box preflight smoke passed for `R1PLAN-bitterroot-nf-12` and
  `R1PLAN-bitterroot-nf-13`: `preflight_ok`, HTTP `206`, `application/pdf`, adapter
  `box_public_file_download`; PDF text confirms the grizzly-bear BA and BO titles, and the BO
  text confirms FWS project code `06E11000-2021-F-0020`.
- Live Kootenai BO chapter preflight passed for `R1PLAN-kootenai-nf-14` through
  `R1PLAN-kootenai-nf-17`: each resolves to `application/pdf`.
- Live targeted closeout preflight passed for the corrected rows: `R1PLAN-nez-perce-clearwater-nfs-04`
  and `R1PLAN-nez-perce-clearwater-nfs-14` resolve through `federal_register_full_text_xml`,
  `R1PLAN-lolo-nf-08` resolves as `application/zip`, and the
  `R1PLAN-nez-perce-clearwater-nfs-18` gap evidence page resolves as `text/html`.

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_adapters_report.py tests/test_download.py tests/test_r1_forest_plan_document_register.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_captured_library.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

This hardening section is retained for source-discovery context. Promotion and controlled
source-delta capture are now implemented in the section above; the next work is extraction/retrieval
readiness for the captured support-document rows, not another register review pass.

## Project SOW Integration Merge

The SOW branch is being integrated through isolated branch
`codex/nepa-project-sow-integration` in worktree
`/Users/chunkstand/projects/usfs-r1-EA-sources-sow-integration`. The branch starts from pushed
`main` at `d55c653` and merges `codex/nepa-project-sow-package` without touching the original
`main` checkout or the SOW worktree. The merge resolution keeps the current East Crazies
review-packet/final-QA state and adds the completed Project SOW planning lane, CLI commands,
architecture ownership, runbook, acceptance matrix, generated brief sources, and tests.

Post-resolution verification target: focused Project SOW/CLI/architecture tests, ruff, compileall,
JSON validation for tracked SOW inputs/schemas, `project-sow-operational-gate`, and `git diff
--check`. The merge should not stage ignored `source_library/` outputs.

## Latest Review Packet Row Completeness Closeout

`docs/REVIEW_PACKET_STRENGTHENING_MILESTONE_PLAN.md` is implemented for the East Crazies proving
review. The review packet now has a generated row inventory, compliance matrix render manifest,
signer-facing review packet index, PDF, and validation sidecar under
`source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/`.

The packet index validates the full current row universe: `37` applicable authority rows, `340`
non-applicable authority boundary rows, `79` Forest Plan component rows, `12` applicable Forest
Plan standards, and all four land-exchange rows with their expected source records
(`R1EA-146`, `R1EA-137`, `R1EA-124`, and `R1EA-150`). The row inventory and packet index now expose
those land-exchange rows as a dedicated first-class section, not only as a subset of general
authority rows. The compliance matrix Markdown now exposes deterministic row markers, and
`compliance_matrix_render_manifest.json` proves `37` authority plus `79` Forest Plan rendered rows.
Root-level `East_Crazies_*` draft exports remain non-canonical.

Regenerated local packet artifacts remain ignored. Latest replay signals:

- `review-packet-index`: passed with `30` checks and `0` failures.
- `ea-consistency-document`: passed with live packet row checks and rewrote the decision-support
  JSON/manifest.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `21/21`, including
  `review_packet_index`.
- `promotion-suite --manifest config/promotion_suite_v1.json`: current promotion passed `31/31`;
  South Plateau remains expansion-only with `forest_plan_reviewer_not_ready`.
- `final-qa-certification`: passed `196/196`; `--validate-only` also passed `196/196`.

Next pass for strengthening the review packet: improve reviewer ergonomics, not row coverage. The
best next slice is a compact reviewer navigation layer over the packet index that groups rows by
authority family, Forest Plan surface, implementation confirmation, and residual risk while keeping
the existing JSON selectors and fail-closed gates as the source of truth.

## Latest East Crazies Land-Exchange Matrix Closeout

All land-exchange authority coverage is now a first-class V1 compliance artifact. The base
`nepa-ea-v0` rule pack has `48` rules, with four land-exchange rows promoted into the matrix
contract:

- `flpma_section_206_land_exchange` (`R1EA-146`)
- `land_exchange_statutory_authorities` (`R1EA-137`)
- `land_exchange_regulatory_requirements` (`R1EA-124`)
- `land_exchange_fs_policy_and_project_references` (`R1EA-150`)

The promoted East Crazy Inspiration Divide review now records `377` candidate authorities, `37`
applicable authorities, `340` non-applicable authorities, `37` generated compliance findings, `162`
generated-pack rule-claim links, and `0` rule-claim gaps. The source-set NEPA 3D graph was also
refreshed to `1,470` nodes, `2,648` edges, `48` base rules, and `211` base rule-claim links; the V1
review overlay validates at `1,996` nodes, `3,550` edges, `377` decisions, and `37` generated
findings.

Intake now identifies land-exchange statutory, regulatory, and Forest Service policy/project cues,
not only FLPMA Section 206. Generated artifacts under
`source_library/reviews/v1-cg-ecid-compliance-review/` were refreshed and remain ignored.
Post row-completeness verification replay is green: `review-packet-index` `30/30`,
`phase-eval` `21/21`, `final-qa-certification` `196/196`,
`final-qa-certification --validate-only` `196/196`, and non-strict `promotion-suite`
current-ready with `31/31` required current-promotion results.

## Latest South Plateau Forest-Plan Context Closeout

`docs/SOUTH_PLATEAU_FOREST_PLAN_CONTEXT_MILESTONE_PLAN.md` is complete in the typed-blocker state.
The resolver now emits `evidence_role` metadata for package location evidence, keeps
bibliographic/background district and forest mentions out of project-location resolution, and uses
selected-profile ranger-district evidence only through profile data.

Live South Plateau artifact state:

- review ID: `region1-expansion-south-plateau-landscape-treatment`
- source set: `source-set-ba8d0feae79501b8`
- package: `26` official PDFs, `3,671` chunks, `0` failed package files
- forest-plan context: `scope_status="custer_gallatin"`, `validation_passed=true`,
  `project_location_signal_count=1`, `geographic_area_count=2`, `management_area_count=9`,
  `overlay_count=4`, `supporting_plan_evidence_count=5`, `unresolved_mention_count=0`
- forest-plan component gate: `329` components, `152` applicable, `58` standards,
  `24` applicable standards, `21` applied standards, `31` gaps, `31` pending
  `missing_package_evidence` component adjudications
- South Plateau phase eval: `15/17`, failing only `compliance_review` and
  `forest_plan_component_adjudication`
- promoted V1 phase eval restored last: `20/20`, `reviewer_ready=true`
- non-strict promotion: `current_promotion_ready=true`, `promotion_ready=true`,
  `failure_category_counts={}`, `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`
- strict expansion: expected command failure with `current_promotion_ready=true`,
  `promotion_ready=false`, `failure_category_counts={"forest_plan_reviewer_not_ready": 6}`

The remaining next implementation target is the `31`-item South Plateau forest-plan component
adjudication worklist:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment \
  --adjudication-file source_library/reviews/region1-expansion-south-plateau-landscape-treatment/forest_plan_component_adjudication.json
```

After adjudication eval passes with `pending_adjudication_count=0` and `system_miss_count=0`, rerun
South Plateau compliance review, South Plateau phase eval, promoted V1 phase eval, strict
promotion, and non-strict promotion.

## Current East Crazies Final QA / Certification Replay Handoff

`docs/EAST_CRAZIES_FINAL_QA_CERTIFICATION_MILESTONE_PLAN.md` is closed. Sequence 0 baseline
replay, Sequence 1 contract/fixture work, Sequence 2 deterministic generator/CLI work,
Sequence 3 gate integration, and Sequence 4 final packet QA/closeout are complete for the promoted
East Crazy Inspiration Divide review.
The lane remains bounded to
`v1-cg-ecid-compliance-review` and source set `source-set-ba8d0feae79501b8`, and it explicitly
avoids broad Region 1 claims, South Plateau blocker resolution, downloader/catalog regeneration,
root-level `East_Crazies_*` draft dependency, or legal sufficiency certification.

The East Crazies compliance-matrix replay refreshed the current gates on 2026-05-08:

- `compliance-review --reuse-package-cache`: refreshed the canonical compliance review and matrix
  family under `source_library/reviews/v1-cg-ecid-compliance-review/`, with
  `reviewer_ready=true`, `validation_passed=true`, `37` generated findings, `37/37` pass
  findings, `340` non-applicable authorities with search coverage, `329` Forest Plan component
  findings, and `12/12` applicable standards applied.
  The generated V1 matrix now includes four first-class land-exchange rows:
  `flpma_section_206_land_exchange` (`R1EA-146`), `land_exchange_statutory_authorities`
  (`R1EA-137`), `land_exchange_regulatory_requirements` (`R1EA-124`), and
  `land_exchange_fs_policy_and_project_references` (`R1EA-150`).
- Land-exchange authority coverage is now first-class at intake as well:
  `applicability-context-build` extracts FLPMA/43 U.S.C. 1716, broader land-exchange statutory
  signals, 36 CFR part 254 regulatory signals, and FSM/FSH land-exchange policy/project signals
  into source-record-bound authority facts before applicability decisions.
- `ea-consistency-document`: refreshed the decision-support JSON, Markdown, PDF, and manifest from
  the refreshed compliance artifacts; the follow-on phase replay validated the report with
  `reviewer_ready=true`.
- `v1-ea-eval --eval-file config/v1_ecid_real_ea_eval.json`: passed with `passed=true`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`.
- `review-packet-index`: passed `30/30`, wrote the ignored packet index family, and validated the
  full `37`/`340`/`79`/`12` row universe.
- `final-qa-certification`: passed `196/196` and refreshed the ignored JSON, Markdown, PDF,
  manifest, and validation family; the follow-up `--validate-only` also passed `196/196` after the
  outer gate replay.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `21/21` phases with
  `review_packet_index`, `final_qa_certification_report`, and `reviewer_ready=true`.
- `promotion-suite --manifest config/promotion_suite_v1.json`: kept current promotion green with
  `current_promotion_ready=true`, `promotion_ready=true`, `31/31` required current-promotion
  results passed, and South Plateau expansion-only blockers still separate as
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`.

The client-sample readability pass on 2026-05-07 refreshed only the canonical matrix rendering from
the existing `compliance_matrix.json`: `compliance_matrix.md` and `compliance_matrix.pdf` now start with
a Responsible Official Readout and deterministic Accuracy Audit in plain decision language, then
render NEPA/authority rows and Forest Plan rows as signer-oriented tables. Each NEPA row now carries
the signer question, record need, decision-support finding, EA evidence excerpt, authority basis,
and trace/caveat status. Each Forest Plan row now carries the component direction, decision-support
status, EA consistency support, Forest Plan basis, and trace/caveat status. The JSON matrix remained
the traceability contract. Follow-on `ea-consistency-document`, `final-qa-certification`,
`phase-eval`, `promotion-suite`, and `final-qa-certification --validate-only` replays are green.

The baseline Sequence 0 replay originally recorded:

- `ea-consistency-document --validate-only`: passed with `reviewer_ready=true`, valid JSON,
  Markdown, PDF, and manifest, current input hashes, `37` applicable authorities, `340`
  non-applicable authorities, `0` unresolved authorities, `377` candidate authorities, `37`
  generated findings, `162` generated-pack rule-claim links, `0` rule-claim gaps,
  `329` Forest Plan component
  rows, `58` Forest Plan standards, `12/12` applicable standards, `43` package files, and `1,265`
  package chunks.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `19/19` phases with
  `reviewer_ready=true`.
- `promotion-suite --manifest config/promotion_suite_v1.json`: kept current promotion green with
  `current_promotion_ready=true`, `promotion_ready=true`, `22/22` required current-promotion
  results passed, and South Plateau expansion-only blockers still separate as
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}` after the later South
  Plateau typed-blocker manifest update.

Current canonical artifact pointers:

- Compliance matrix Markdown:
  `source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.md`
  (`sha256=241ac87038ce3660ce18d5f35060d03b43b2d6540b7380dbc3f292e02dc7987a`)
- Compliance matrix PDF:
  `source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.pdf`
  (`sha256=d117093c64f879964ad08bdddb68a07b0c85d1f8b023e36aff7db3c51d800461`)
- Decision-support JSON:
  `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/ea_consistency_decision_support.json`
  (`sha256=4986087120612f76c579fa0c64d375f5b5e35a21c41a795fcdb30153fa53b768`)
- Decision-support Markdown:
  `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/ea_consistency_decision_support.md`
  (`sha256=76f7f9c0e202f823350c6c7dd2ea01c1d0fd745745637eacaebbc3025ba27d07`)
- Decision-support PDF:
  `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/ea_consistency_decision_support.pdf`
  (`sha256=20a0e615e4b9f7b552044d430a356e4ccdec31e22ca3e078d59cce71d3623f9f`)
- Decision-support manifest:
  `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/ea_consistency_decision_support_manifest.json`
  (`sha256=185de3fabf5ad87f9a0dda705f747b6ae46db62073b28cb179989bb7b2d31a60`)
- Review-scoped phase eval:
  `source_library/reviews/v1-cg-ecid-compliance-review/phase_eval_results.json`
  (`sha256=c991e065b44a773b9add0076fc1f63bdebba31d9fde52affc07e6616b8787463`)
- Non-strict promotion suite:
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  (`sha256=d196b50caf6bbc148f120ee651ef3759aa3e415a75ae75dea737b6414dfe15fe`)
- Final QA validation sidecar:
  `source_library/reviews/v1-cg-ecid-compliance-review/final_qa/east_crazies_final_qa_certification_validation.json`
  (`sha256=1ce414c36a378daa5515dc9d77995685d73fbff77680604db5acf42d6a20ca83`)

Sequence 1 added:

- `config/east_crazies_final_qa_certification_v1.json`
- `config/fixtures/final_qa/v1_ecid_final_qa_expected_summary.json`
- `tests/fixtures/final_qa/minimal_final_qa_certification_report.json`
- `tests/test_final_qa_certification.py`
- the final QA schema section in `docs/OUTPUT_SCHEMAS.md`

The contract pins semantic counts, source selectors, current artifact hashes, required gate names,
selected Markdown/PDF rendering requirements, optional reviewer signoff fields, accepted V1 risk
visibility, and fail-closed categories. It does not pin full rendered Markdown/PDF body text.
The Sequence 1 gap-close pass tightened the contract so every scalar expected-summary count appears
in `required_count_fields`, config and expected-summary section/output/failure-category contracts
are tested for alignment, and `validation_expectations` maps the Sequence 1 acceptance criteria to
fail-closed categories before the Sequence 2 generator implementation. Sequence 1 gap-close
verification passed: `tests/test_final_qa_certification.py` (`8 passed`),
`tests/test_architecture_contract.py` (`5 passed`), and `git diff --check`.

Sequence 2 added:

- `src/usfs_r1_ea_sources/final_qa_certification.py`
- `src/usfs_r1_ea_sources/cli_final_qa.py`
- `final-qa-certification` CLI registration
- architecture-contract ownership for the final QA module, command, and ignored artifact family
- focused generator/CLI tests in `tests/test_final_qa_certification.py` and `tests/test_cli.py`

The live Sequence 2 generation command passed `157/157` checks and wrote ignored outputs under
`source_library/reviews/v1-cg-ecid-compliance-review/final_qa/`. The follow-up `--validate-only`
command also passed `157/157` checks without rewriting outputs. The reader validates pinned input
hashes, required gate selectors, review/source-set identity, semantic counts, configured source
selectors, PDF headers, accepted V1 risk visibility, legal-conclusion safeguards, and the
non-canonical root-level draft boundary. The Sequence 2 gap-close pass tightened acceptance
alignment by carrying all `37` compliance-matrix authority findings in `finding_qa.findings`, each
with a compliance-matrix selector, package/source evidence pointers, and trace IDs, instead of only
a representative finding row.

Sequence 3 added:

- `east_crazies_final_qa_certification_validation.json` as the generated validation sidecar;
- optional review-scoped `phase-eval` phase `final_qa_certification_report` when the sidecar exists;
- current-promotion-suite required artifacts for the final QA JSON, manifest, PDF, and validation
  sidecar;
- self-reference handling so final QA validation still passes when the only hash/count drift is the
  passing outer final QA phase and the four passing final QA promotion-suite gates.

Sequence 3 gap-close tightened sidecar freshness: the validation sidecar now records SHA-256 hashes
for the generated JSON, Markdown, PDF, and manifest, and `promotion-suite` compares those declared
hashes back to the local files before the current-promotion gate can pass. This prevents a stale
passing validation sidecar from masking a later edited packet file.

Latest Sequence 3 verification:

- `final-qa-certification`: passed `166/166` and wrote the ignored JSON, Markdown, PDF, manifest,
  and validation family.
- `final-qa-certification --validate-only`: passed `166/166` without rewriting outputs.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `20/20` with
  `final_qa_certification_report` and `reviewer_ready=true`.
- `promotion-suite --manifest config/promotion_suite_v1.json`: passed current promotion with
  `26/26` required current-promotion results, `current_promotion_ready=true`,
  `promotion_ready=true`, and South Plateau blockers separate as
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`.
- strict expansion `promotion-suite --strict-expansion` failed as expected with
  `current_promotion_ready=true`, `promotion_ready=false`, and the same South Plateau
  `forest_plan_reviewer_not_ready` blockers.

Sequence 4 is complete. It closed the final packet QA pass by making the rendered Machine Replay
summary show both baseline counts that exclude final-QA self-reference and live integrated counts.
After the row-completeness closeout those current counts are `20/20` baseline phase eval, `27/27`
baseline current-promotion results, `21/21` live phase eval, and `31/31` live current-promotion
results. It also made `v1-ea-eval` idempotent for unchanged semantic payloads so replaying that
gate does not churn the final QA input hash only by updating `generated_at`.

Latest Sequence 4 verification:

- `v1-ea-eval --eval-file config/v1_ecid_real_ea_eval.json`: passed with
  `passed=true`, `broader_ea_passed=true`, and `forest_plan_passed=true`.
- `final-qa-certification`: passed `166/166` and wrote the ignored JSON, Markdown, PDF, manifest,
  and validation family after the V1 eval refresh.
- `final-qa-certification --validate-only`: passed `166/166` before and after the outer gate replay.
- Rendered packet inspection: Markdown exposes required caveats, source pointers, accepted V1 risk
  ledger, residual blockers, and root-level draft exclusion; PDF is `%PDF-1.4`.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `20/20` with
  `final_qa_certification_report` and `reviewer_ready=true`.
- `promotion-suite --manifest config/promotion_suite_v1.json`: passed current promotion with
  `26/26` required current-promotion results, `current_promotion_ready=true`,
  `promotion_ready=true`, and South Plateau blockers separate as
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`.

Pre-review-packet final closeout replay:

- `v1-ea-eval --eval-file config/v1_ecid_real_ea_eval.json`: passed with
  `passed=true`, `broader_ea_passed=true`, and `forest_plan_passed=true`.
- `final-qa-certification`: passed `168/168` and refreshed the ignored JSON, Markdown, PDF,
  manifest, and validation family.
- `final-qa-certification --validate-only`: passed `168/168` without rewriting outputs after the
  outer gate replay. The stored validation sidecar records the inner packet replay at `159/159`;
  the CLI result adds the outer self-reference/freshness and required-row checks.
- Rendered packet inspection: Markdown exposes the required caveats, source pointers, accepted V1
  risk ledger, residual blockers, baseline/live gate counts, and root-level draft exclusion; PDF
  header is `%PDF-1.4`.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `20/20` with
  `final_qa_certification_report` and `reviewer_ready=true`.
- Strict expansion `promotion-suite --strict-expansion` failed as expected with
  `current_promotion_ready=true`, `promotion_ready=false`, and
  `failure_category_counts={"forest_plan_reviewer_not_ready": 6}`.
- Non-strict `promotion-suite` was rerun last and passed with `current_promotion_ready=true`,
  `promotion_ready=true`, `failure_category_counts={}`, and
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`.

The East Crazies final QA/certification replay milestone has no remaining planned sequence. Next
implementation target, if continuing strict expansion, is the South Plateau `31`-item forest-plan
component adjudication worklist. Root-level `East_Crazies_*` drafts remain non-canonical and
unstaged.

## Integrated Project SOW Branch Handoff

## Scope of Work Capabilities Brief

A generated 2-page system-level scope of work capabilities brief now lives at
`docs/capabilities/project_sow_capabilities_brief.pdf`, with matching HTML at
`docs/capabilities/project_sow_capabilities_brief.html` and generated figures under
`docs/capabilities/assets/`. It mirrors the style of
`docs/capabilities/nepa_3d_capabilities_brief.pdf` while keeping the content shorter and focused on
the system design and capabilities for producing scopes of work from structured proposed-action
intake.

The brief was regenerated by `tools/build_project_sow_capabilities_brief.mjs` and verified with a
fresh local operational gate run to `/tmp/project-sow-capabilities-gate`. The polished brief is intentionally
general: page one uses overall system facts instead of project-example metric tiles, the delivery
stack uses only stage labels, and a purpose section explains the scope-development bottleneck and
the system boundary between required work and preference-driven additions. Page two consolidates
intake tracing, work package rendering, reviewer adjudication, and EA assembly handoff into one
system-capability view.

Boundary: this is a planning and contracting support brief. It does not change package
generation code, generated source-library policy, applicability decisions, compliance findings,
legal advice, legal sufficiency, or final agency decision status.

## East Crazies Soils Resource Area SOW

An ad hoc soils resource-area SOW has been produced at
`docs/EAST_CRAZIES_SOILS_RESOURCE_AREA_SOW.md`, with a PDF rendering at
`docs/EAST_CRAZIES_SOILS_RESOURCE_AREA_SOW.pdf` and a styled HTML companion at
`docs/EAST_CRAZIES_SOILS_RESOURCE_AREA_SOW.html`. The styled outputs are regenerated by
`tools/build_east_crazies_soils_sow.mjs`, which renders the Markdown into a compact professional
layout and verifies the PDF stays at 10 pages or fewer; the current readability pass removes most
boxed treatments, uses larger single-column body text, renders Appendix A as ruled crosswalk rows,
and produces a 7-page PDF. It is grounded in the current Project SOW package docs,
`config/project_sow_resource_scopes_v1.json`, the East Crazies intake fixture, and a temporary East
Crazies package smoke run under `/tmp/east-crazies-soils-sow-package/`.

The SOW has been revised into a WLG-facing new-project example with a short header followed
immediately by a three-part Deliverables section: Fieldwork, Analysis, and Reporting. The rest of
the document now mirrors that structure with Fieldwork/Data Collection, Analysis Output, and
Reporting Output sections before Appendix A and Sources Cited. It demonstrates that the system can
produce resource-area scopes of work for a new NEPA project from structured intake before late-stage
NEPA materials or resource-analysis packages exist. The source stack remains explicit: current USDA
NEPA procedures, NFMA/planning-rule requirements, Forest Service handbook/manual direction, Region 1
soil management direction, the applicable Forest Plan, soil-quality monitoring methods, National
BMPs, and official soil-survey data. East Crazies is used as the concrete example action, not as a
completed-document review. The Fieldwork/Data Collection section now describes existing soil
condition data collection, prioritization for disturbed or sensitive areas and higher ground
disturbance, and methodology tied to R1 Soil Quality Standards, NFMA, and the Custer Gallatin Land
Management Plan. It names DSD surveys and other policy-triggered soil survey types with short
descriptions. Analysis still uses Appendix A as the authority-to-report control table from source
trigger to required report output and acceptance test. The current-regulation audit keeps the SOW
within USDA NEPA procedure scope by removing non-regulatory issue-screening language, old
direct/indirect/cumulative-effects framing, comment-response artifacts, and stale Forest Service NEPA
directive links. It keeps only the FS and Forest Plan soil guidance that applies to a soils resource
report: R1 FSM 2550 soil-quality direction, Custer Gallatin soil plan components, soil-disturbance
methods, official soil-survey data, and National BMPs. The top deliverables section has been reduced
to a simple requirements list, leaving detailed explanations in the later Fieldwork, Analysis,
Reporting, and Appendix sections. The header has been shortened to essential metadata, a scope line
for applicable current NEPA and USDA regulations plus the Custer Gallatin Land Management Plan, and
a brief proposal-record support sentence; the project-drivers paragraph was removed.

Important boundary: this is a generated SOW example, not an East Crazies compliance review or a
statement that completed East Crazies materials are required for new-project SOW generation.
This artifact does not change package-generation code, generated source-library policy,
applicability decisions, compliance findings, legal sufficiency, or final agency decision status.

## Current Project SOW Package Branch Handoff

Branch/worktree:

- Branch: `codex/nepa-project-sow-package`
- Worktree: `/Users/chunkstand/projects/usfs-r1-EA-sources-nepa-project-sow-package`

Project SOW operationalization Sequence 1 is implemented. The supported first step for a new
land-exchange proposed action is now to start from
`config/templates/project_sow_land_exchange_intake_template.json`, populate the project-specific
fields, then run the no-write validator:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-intake-validate \
  --intake /tmp/new_land_exchange_intake.json
```

The package command also supports `--validate-only` for the same validation path. Both validation
paths reuse the package builder's intake checks and do not create
`source_library/projects/<project_id>/requirements_package/` outputs. The validation summary has
schema version `project-sow-intake-validation-summary-v0`, reports selected scope IDs, proposed
action resource-area count, intake evidence graph node/edge counts, all validation checks, failed
checks, and `output_written=false`. The tracked intake schema is
`docs/schemas/project_sow_intake_v0.schema.json`. The alignment pass after the first Sequence 1
commit added explicit nested schema-shape validation so incomplete action-element, evidence-ref,
federal-land-action, resource-expectation, and observed-report rows fail before package generation.

Sequence 1 validation fixtures now cover unsupported schema version, missing federal land action,
missing action elements, missing or incomplete evidence refs, incomplete observed-report rows, and
unknown resource-area IDs. The minimal land-exchange template validates with `4` selected SOW
scopes, `2` proposed-action resource areas, and `0` validation failures. The East Crazies intake
validates without writing outputs and preserves the accepted calibration counts: `10` selected SOW
scopes, `23` proposed-action resource areas, `115` graph nodes, `134` graph edges, and `0`
validation failures.

Project SOW operationalization Sequence 2 is implemented. The new public command is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-intake-draft \
  --proposed-action /tmp/proposed_action.txt \
  --output /tmp/new_land_exchange_draft_intake.json \
  --forest "Example National Forest" \
  --district "Example Ranger District"
```

The command drafts a `project-sow-intake-v0` JSON artifact from proposed-action text using
`config/project_sow_intake_draft_rules_v1.json`. Draft output is intentionally unreviewed:
`draft_metadata.review_status=unreviewed`,
`draft_metadata.reviewer_confirmation_required=true`, and `uncertainty_flags[]` keep candidate
resource areas and federal land actions in reviewer-confirmation work. `project-sow-intake-validate`
fails such drafts on `draft_reviewer_confirmation_complete` until a reviewer confirms the draft,
sets `reviewer_confirmation_required=false`, and clears uncertainty flags. The draft preserves the
proposed-action source path, source text hash, and paragraph locators in `draft_metadata` and
evidence refs. The draft command reports success only when reviewer confirmation is the sole
validation blocker; unrelated schema, scope, or inventory failures are reported in
`unexpected_failed_validation_checks`. It does not create applicability decisions, compliance
findings, legal advice, legal sufficiency conclusions, or final agency decisions.

The Sequence 2 alignment pass closed the remaining draft-contract gap by declaring
`draft_metadata` in `docs/schemas/project_sow_intake_v0.schema.json` and tightening the fixture test
to verify the exact proposed-action source path and SHA-256 hash.

Sequence 2 fixtures now include a Red Rock Ridge land-exchange proposed-action text fixture, an
ambiguous land-adjustment fixture, and expected draft metadata for the positive case. Focused tests
cover draft generation, ambiguity flags, unreviewed-draft validation failure, and reviewer-confirmed
draft validation replay, plus a guard that unexpected draft-validation failures return a failing
status.

Project SOW operationalization Sequence 3 is implemented. The new public command is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-eval \
  --output-dir /tmp/project_sow_eval
```

The command reads `config/project_sow_eval_proving_intakes_v1.json`, runs three proving intakes in
one command, writes local generated packages under `<output-dir>/cases/<case_id>/`, and writes
`project_sow_eval_summary.json`. The tracked cases are East Crazies, Red Rock Ridge, and Silver
Creek. The summary compares actual metrics to tracked expected values and keeps diagnostics
separate: system misses, intake omissions, calibration gaps, and expected no-observed-report cases.
The accepted Sequence 3 smoke signal is `3` cases passed, `0` failed cases, `0` system misses, `0`
intake omissions, `7` East Crazies calibration gaps, and `17` expected no-observed-report rows
across the two new proving intakes. East Crazies remains green at `10` scopes, `23`
proposed-action resource areas, `115` graph nodes, `134` graph edges, and `0` validation failures.

Project SOW operationalization Sequence 4 is implemented. Resource scope templates in
`config/project_sow_resource_scopes_v1.json` now carry contract-ready assumptions, dependencies,
optional deliverables, acceptance criteria, reviewer role, review timing, and reviewer signoff fields
for every configured scope. The canonical `resource_scope_records[]` include those fields, and the
Markdown/PDF renderings separate required deliverables from optional deliverables and add a
`Contract terms` section without replacing the JSON contract. Package validation now includes
`selected_resource_scopes_have_contract_fields`, and tests prove optional deliverables do not satisfy
the required deliverable gate. The package remains a planning and contracting support artifact for
resource SOW scoping, not a final SOW award document, applicability decision, compliance finding,
legal advice, legal sufficiency conclusion, or final agency decision.

Sequence 4 closeout verification passed: the focused project-SOW/CLI/architecture tests reported
`46 passed`; the East Crazies package smoke run to `/tmp/project-sow-sequence-4-package` selected
`10` scopes, found `23` proposed-action resource areas, emitted `115` graph nodes and `134` graph
edges, reported `0` validation failures, and produced a valid `%PDF-` header; the three-case
`project-sow-eval` smoke run to `/tmp/project-sow-sequence-4-eval` reported `3` cases passed and
`0` failed cases.

The Sequence 3/4 alignment pass closed two gaps. First, `project-sow-eval` now reports and checks
contract-readiness metrics for selected-scope contract fields, contract-ready scope count, required
deliverable scope count, and optional deliverable scope count across all three proving intakes.
Second, the handoff labels below now distinguish the earlier requirements-package sequence numbers
from the current operationalization sequence numbers so the next operational pass remains Sequence
5 reviewer adjudication.

Alignment verification passed: the focused project-SOW/CLI/architecture suite reported
`47 passed`; `project-sow-eval` reported `3` cases passed, `0` failed cases,
`contract_fields_passed=true` for all cases, and contract-ready/required-deliverable/optional
deliverable scope counts matching selected scope counts for East Crazies (`10`), Red Rock Ridge
(`7`), and Silver Creek (`9`).

Project SOW operationalization Sequence 5 is implemented. The new public commands are:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-template \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir /tmp/project-sow-sequence-5-adjudication
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-eval \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --adjudication /tmp/project-sow-sequence-5-completed-adjudication.json
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-apply \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --adjudication /tmp/project-sow-sequence-5-completed-adjudication.json \
  --output-intake /tmp/project-sow-sequence-5-adjudicated-intake.json
```

The template/worklist exports unresolved resource areas, missing evidence refs, unknown
resource-area IDs, calibration gaps, and optional deliverable decisions. East Crazies currently
exports a `37`-item queue: `7` calibration gaps and `30` optional-deliverable decisions. The eval
fails targeted rows for stale hashes, missing queue rows, unexpected or duplicated rows, invalid
item types, invalid decisions, pending decisions, or incomplete reviewer metadata. Apply reruns eval
and writes a new adjudicated intake copy with `project_sow_adjudication` replay metadata only when
the eval passes. Package generation from that adjudicated intake surfaces
`adjudication_status=adjudicated` and deterministic decision counts in `intake_summary` and
`reviewer_summary.snapshot`. The adjudication loop remains a project-SOW planning overlay; it does
not create applicability decisions, compliance findings, legal advice, legal sufficiency
conclusions, or final agency decisions, and it does not edit generated package outputs by hand.

Sequence 5 closeout verification passed: the focused project-SOW/CLI suite reported `49 passed`,
and the architecture contract reported `5 passed`; the East Crazies adjudication-template smoke run
wrote a `37`-item worklist; an unedited-template eval failed as expected with `37` pending
adjudications; a completed-adjudication eval passed with `7` accepted calibration gaps and `30`
out-of-scope optional-deliverable decisions; adjudication apply wrote an adjudicated intake copy;
package generation from that copy
reported `adjudication_status=adjudicated`, selected `10` scopes, found `23` proposed-action
resource areas, preserved `115` graph nodes and `134` graph edges, reported `0` validation
failures, and produced a valid `%PDF-` header. The three-case `project-sow-eval` smoke run reported
`3` cases passed and `0` failed cases.

Sequence 5 gap-close pass is implemented. `project-sow-adjudication-eval` now requires complete
top-level `reviewer_metadata`, treats current-queue identity fields as immutable, and fails stale
hashes or tampered rows before replay. `project-sow-adjudication-apply` preserves the top-level
reviewer metadata in the adjudicated intake copy, and validation/package summaries now expose
`adjudication_status`, `adjudication_item_count`, and `adjudication_decision_counts`. Gap-close
regressions cover stale input hashes, row identity tampering, missing reviewer metadata, and
summary-level adjudication status/counts. Gap-close verification passed: the focused
project-SOW/CLI suite reported `51 passed`; architecture contract reported `5 passed`; ruff,
compileall, JSON validation, and `git diff --check` passed; the three-case `project-sow-eval`
smoke reported `3` cases passed and `0` failed cases; the adjudication replay smoke wrote a
`37`-item worklist, preserved top-level reviewer metadata, replayed `7` accepted calibration gaps
and `30` out-of-scope optional-deliverable decisions, and generated a package with
`adjudication_status=adjudicated` plus a valid `%PDF-` header.

Project SOW operationalization Sequence 6 is implemented. The new public command is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-ea-package-handoff \
  --package source_library/projects/<project_id>/requirements_package/project_sow_package.json
```

The command reads canonical `project_sow_package.json` plus
`config/project_sow_ea_handoff_rules_v1.json` and writes
`project_sow_ea_package_handoff.json` plus `project_sow_ea_package_handoff.md` next to the package
unless explicit output paths are supplied. The JSON handoff records package identity, package/rules
input paths and hashes, downstream boundaries, category summaries, validation checks, and future EA
assembly slots. Slots map selected resource scopes to expected source collection, specialist report
production, public involvement, consultation, Forest Plan consistency, and decision-record support
artifacts, but every slot has `future_artifact_required_now=false`.

Sequence 6 closeout verification passed: the focused project-SOW/CLI suite reported `55 passed`,
and the CLI smoke run generated a handoff from the East Crazies package with `27` expected
future-artifact slots: `10` source-collection, `10` specialist-report-production, `1`
public-involvement, `3` consultation, `1` Forest Plan consistency, and `2`
decision-record-support slots. The handoff remains upstream planning support only; it does not
create applicability decisions, generated rule packs, compliance findings, legal advice, legal
sufficiency conclusions, or final agency decisions.

Sequence 6 gap-close pass is implemented. `project_sow_ea_package_handoff.json` now includes a
machine-readable `downstream_consumption_contract` naming the fields future commands may consume
and the conclusions they must not infer. Handoff validation now fails closed on incomplete category
metadata, unsupported `applies_to` values, empty expected artifact types, incomplete rule
scope/resource-area bindings, incomplete or duplicate downstream boundaries, empty handoff slots,
or future-artifact entries that are missing artifact types or do not preserve `required_now=false`.
Gap-close regression coverage proves malformed handoff rules fail without writing JSON or Markdown
handoff outputs while the East Crazies contract stays stable at `27` expected future-artifact slots.
Gap-close verification passed: the focused project-SOW/CLI suite reported `56 passed`;
architecture contract reported `5 passed`; ruff, compileall, JSON validation, and
`git diff --check` passed; the East Crazies package and handoff smoke generated `27`
future-artifact slots with `12` passing handoff validation checks; and the three-case
`project-sow-eval` smoke reported `3` cases passed, `0` failed cases, `0` system misses, and `0`
intake omissions.

Project SOW operationalization Sequence 7 is implemented. The new local-only operational gate is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-operational-gate \
  --output-dir source_library/project_sow_operational_gate
```

The gate validates the minimal template and all proving intakes without writing package outputs,
runs the three-case `project-sow-eval`, verifies proving package rendering/PDF smoke signals,
runs an East Crazies EA handoff smoke, checks tracked JSON inputs and docs references, and writes
`project_sow_operational_gate_summary.json` plus
`project_sow_operational_readiness_report.md` under the selected output directory. Sequence 7 keeps
the command local-only; CI integration remains a separate future milestone. The tracked closeout
report is `docs/PROJECT_SOW_OPERATIONAL_READINESS_REPORT.md`.
Sequence 7 closeout verification passed: the focused project-SOW/CLI suite reported `59 passed`;
architecture contract reported `5 passed`; ruff, compileall, JSON validation, and
`git diff --check` passed; the operational gate run to
`/tmp/project-sow-sequence-7-operational-gate` passed `4` validation-only intake targets, `3`
proving eval cases, `0` failed cases, `0` system misses, `0` intake omissions, and an East Crazies
EA handoff smoke with `27` expected future-artifact slots and `0` handoff validation failures.

Sequence 7 gap-close pass is implemented. `project_sow_operational_gate_summary.json` now includes
a machine-readable `closeout_contract`, expands durable-doc checks to README, architecture,
current-state, output-schema, runbook, milestone, session handoff, architecture contract, and
readiness-report docs, and records output hashes for the operational readiness report, gate summary
content, proving eval summary, and EA handoff smoke artifacts. Regression coverage proves the gate
fails closed when a required closeout-doc reference is missing. Gap-close verification passed: the
focused project-SOW/CLI suite reported `60 passed`; architecture contract reported `5 passed`;
ruff, compileall, JSON validation, and `git diff --check` passed; the operational gate run to
`/tmp/project-sow-sequence-7-gap-gate` passed `4` validation-only intake targets, `3` proving eval
cases, `0` failed cases, `0` system misses, `0` intake omissions, `13` gate checks, and an East
Crazies EA handoff smoke with `27` expected future-artifact slots and `0` handoff validation
failures.

Project SOW operationalization milestone closeout alignment is implemented. The tracked acceptance
matrix is `docs/PROJECT_SOW_OPERATIONALIZATION_ACCEPTANCE_MATRIX.md`; it maps Sequences 1 through 7
to acceptance criteria, verification evidence, and status, and the operational gate now checks that
matrix as part of the durable-doc closeout set. Milestone closeout verification passed: the focused
project-SOW/CLI suite reported `60 passed`; architecture contract reported `5 passed`; ruff,
compileall, JSON validation, and `git diff --check` passed; the operational gate run to
`/tmp/project-sow-milestone-closeout-gate` passed `4` validation-only intake targets, `3` proving
eval cases, `0` failed cases, `0` system misses, `0` intake omissions, `13` gate checks, and an
East Crazies EA handoff smoke with `27` expected future-artifact slots and `0` handoff validation
failures. A full repo `pytest` run was also attempted and reached `427 passed`, `6 skipped` before
failing the non-Project-SOW
`tests/test_authority_family_rule_templates.py::test_authority_family_templates_have_milestone_3_contracts`
because the ignored generated catalog file
`source_library/catalog/source_catalog.jsonl` is absent from this worktree; generated
`source_library/` evidence remains unstaged by policy.

The earlier Project SOW requirements-package milestone is implemented for the
proposed-action-to-resource-SOW lane. That baseline intentionally stays upstream of South Plateau
applicability closure and does not read or write South Plateau review outputs. The public package
command is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-package \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir source_library
```

Implemented surfaces:

- `config/project_sow_resource_scopes_v1.json`
- `config/project_sow_intake_draft_rules_v1.json`
- `config/project_sow_eval_proving_intakes_v1.json`
- `config/project_sow_ea_handoff_rules_v1.json`
- `config/fixtures/project_sow/east_crazies_land_exchange_intake.json`
- `config/fixtures/project_sow/red_rock_ridge_land_exchange_intake.json`
- `config/fixtures/project_sow/silver_creek_access_land_adjustment_intake.json`
- `config/fixtures/project_sow/proposed_action_text/red_rock_ridge_land_exchange_proposed_action.txt`
- `config/fixtures/project_sow/proposed_action_text/ambiguous_land_adjustment_proposed_action.txt`
- `config/fixtures/project_sow/proposed_action_text/red_rock_ridge_expected_draft_metadata.json`
- `src/usfs_r1_ea_sources/project_sow_package.py`
- `src/usfs_r1_ea_sources/cli_project_planning.py`
- `tests/test_project_sow_package.py`
- `tests/test_cli.py`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/ARCHITECTURE.md`
- `docs/architecture_contract.toml`
- `docs/PROJECT_SOW_REQUIREMENTS_PACKAGE_MILESTONE_PLAN.md`
- `docs/PROJECT_SOW_OPERATIONALIZATION_MILESTONE_PLAN.md`
- `docs/PROJECT_SOW_PACKAGE_RUNBOOK.md`
- `docs/schemas/project_sow_intake_v0.schema.json`
- `config/templates/project_sow_land_exchange_intake_template.json`

The command writes `project_sow_package.json`, `project_sow_package.md`,
`project_sow_package.pdf`, and `project_sow_package_manifest.json` under
`source_library/projects/<project_id>/requirements_package/`. A local CLI smoke run to `/tmp`
selected ten East Crazies land-exchange resource scopes: NEPA project management, lands/realty,
Forest Plan consistency, wildlife/species/botany, cultural/tribal, hydrology/wetlands/water
quality, roads/access/recreation/designated areas, vegetation/soils/air-quality/climate/carbon,
minerals/energy/hazardous materials, and public involvement/coordination.

Earlier requirements-package Sequence 2 added an East Crazies calibration comparison. The intake
now records structured `proposed_action_elements`, `resource_analysis_expectations`, and observed
specialist/supporting reports from the completed East Crazies package. The generated JSON/Markdown
now includes a `resource_analysis_matrix` that compares proposed-action-derived resource areas to
selected resource scopes and the observed report set: mineral potential, aquatics, at-risk
plants/botany, carbon, cultural resources, recreation special areas, recreation special uses,
roads/trails/access, tribal relations, wetlands, wildlife, water rights, and the plan-consistency
table. Validation fails if an observed report resource area is not derived from the proposed action
or lacks selected resource scope coverage.

Earlier requirements-package Sequence 3 added a package-local `intake_evidence_graph` to
`project_sow_package.json` and a concise graph projection to `project_sow_package.md`. The East
Crazies fixture now carries `evidence_refs` for proposed-action elements and observed
specialist/supporting reports. Validation
now fails closed on duplicate intake-derived graph IDs before graph assembly deduplicates nodes and
edges, dangling graph edges, action elements with resource areas but no evidence refs,
proposed-action resource areas without the canonical graph path, and observed report resource areas
without proposed-action support.

The required planning path is:

```text
proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope
```

A local requirements-package Sequence 3 CLI smoke run to `/tmp` selected `10` resource scopes, found
`23` proposed-action resource areas, emitted `115` graph nodes and `134` graph edges, and reported
`0` validation failures.

Earlier requirements-package Sequence 4 hardened the graph-quality fixture set. Focused tests now
cover missing proposed-action evidence refs, observed reports with no proposed-action support,
proposed-action resource areas with no configured resource scope, evidence-bearing action elements with
no triggered resource area, duplicate observed-report graph IDs, duplicate required-deliverable
graph IDs, dangling graph edges, and land-exchange intakes with no federal land action. A local
requirements-package Sequence 4 CLI smoke run to `/tmp` preserved the same accepted East Crazies
counts: `10` resource scopes, `23` proposed-action resource areas, `115` graph nodes, `134` graph edges,
and `0` validation failures.

Earlier requirements-package Sequence 5 added the reviewer-facing polish pass. The canonical JSON
now includes `reviewer_summary`; Markdown now starts with a reviewer snapshot, review checklist,
package boundaries, and compact tables; the command writes `project_sow_package.pdf` from the same
package JSON; rendering validation checks fail if required Markdown or PDF sections are missing;
and the tracked runbook `docs/PROJECT_SOW_PACKAGE_RUNBOOK.md` documents how to create a new
land-exchange intake. The post-sequence alignment pass verifies that generated PDF bytes include
reviewer-facing content and validation checks from the package rendering, and it clarifies that
reviewer-summary unresolved resource areas are separate from calibration gaps where scope of work content is
required but no observed East Crazies report was supplied. A local requirements-package Sequence 5
CLI smoke run to `/tmp` preserved `10` resource scopes, `23` proposed-action resource areas, `115` graph
nodes, `134` graph edges, `0` validation failures, and a valid `%PDF-` header.

The dedicated sequence plan is now `docs/PROJECT_SOW_REQUIREMENTS_PACKAGE_MILESTONE_PLAN.md`.
The successor operationalization plan is
`docs/PROJECT_SOW_OPERATIONALIZATION_MILESTONE_PLAN.md`. Next project-SOW sequence: Sequence 7,
operational gate and release closeout. Keep JSON canonical, do not convert resource scopes into
applicability or compliance findings, and do not stage ignored `source_library/` outputs.

## Current Applicability/Expansion Handoff

`docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` is complete through Sequence 7 for the
declared ECID preliminary-EA and South Plateau real-package expansion set. The South Plateau Area
Landscape Treatment Project package exists locally as
`region1-expansion-south-plateau-landscape-treatment`: `26` official PDFs were imported from the
official project Box folder into
`source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment`, with an
ignored `box_import_manifest.json` recording Box IDs, source URLs, byte sizes, and hashes. The
package cache was rebuilt with `.venv-docling`; `26/26` files extracted, `0` failed, and `3,671`
chunks were written under
`source_library/reviews/region1-expansion-south-plateau-landscape-treatment/package/`.

South Plateau applicability validation now passes after replayable adjudication: `61` authorities
are applicable, `331` are non-applicable, `0` are unresolved or `needs_adjudication`, and
`generated_rule_pack_ready=true`. `applicability-generate-rule-pack` passed with `61` generated
rules and generated pack hash `39663183f91ad309fcfad60a17d0d88b371e184df8f06664cadd612b5c7aebec`.
South Plateau compliance review now resolves Custer Gallatin forest-plan context but fails the
required component gate: `61` authority findings still emit with `41` pass, `19` uncertain, `1`
gap, `280` rule-claim links, and `0` rule-claim gaps, while forest-plan component evaluation
records `31` pending `missing_package_evidence` adjudication items. South Plateau review-scoped
phase eval is `15/17` with blockers limited to `compliance_review` and
`forest_plan_component_adjudication`.

`config/promotion_suite_v1.json` now includes South Plateau as a required expansion review case
with generated rule-pack, compliance validation, matrix/PDF, authority sidecar, litigation-risk,
forest-plan context summary, component findings, component reviewer queue, component adjudication
template/eval, and review-scoped phase-eval checks. The South Plateau expansion slot is
`ready=false` with `failure_category="forest_plan_reviewer_not_ready"`: it declares
`forest_plan_profile="custer_gallatin"` and now matches `scope_status="custer_gallatin"` with
context validation passed, but it remains not reviewer-ready until the `31` component
adjudications are completed.

Strict expansion promotion was written to
`source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion/` and
now fails as expected with `current_promotion_ready=true`, `promotion_ready=false`,
`expansion_ready=false`, `expansion_artifacts_ready=false`,
`failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
`expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
`open_expansion_artifact_count=5`, and `open_expansion_slot_count=1`. Non-strict promotion was rerun
last and keeps the current V1 promotion green with `current_promotion_ready=true`,
`promotion_ready=true`, `failure_category_counts={}`, and the same expansion-only blocker counts.
The promoted V1 review-scoped phase eval was rerun after South Plateau review-scoped eval to
restore the shared current-promotion phase artifact at `20/20`.

Sequence 7 alignment closeout added direct regression coverage for the
`forest_plan_component_gate_required=true` branch: a declared-profile slot cannot pass strict
expansion without a `forest_plan_component_eval` or `forest_plan_component_adjudication` phase.
The milestone plan also now labels the Sequence 6 strict-pass evidence as historical and superseded
by the Sequence 7 forest-plan blocker. No generated artifact state changed in that alignment pass.

The ECID preliminary-EA expansion slot remains ready. Its Forest Plan component adjudication eval
for the current `158`-row queue resolves all `158` rows as true EA package-evidence omissions,
`pending_adjudication_count=0`, and `system_miss_count=0`; those adjudications keep the missing
package evidence visible as gaps and do not mark components supported or create legal conclusions.
ECID compliance review reports `reviewer_ready=true`, ECID review-scoped phase eval passes `16/16`,
and the required ECID expansion artifacts pass.

Next implementation target if continuing strict expansion: complete the South Plateau
`forest_plan_component_adjudication_template.json` worklist as a reviewed
`forest_plan_component_adjudication.json`, then rerun component adjudication eval and downstream
South Plateau/V1 promotion gates.

## Current NEPA 3D Graph Gate Handoff

NEPA 3D Milestone 7 has its initial graph validation and promotion-gate pass implemented for
`source-set-ba8d0feae79501b8` and `v1-cg-ecid-compliance-review`. Graph validation checks now carry
graph-specific failure categories, validation and summary artifacts record
`failure_category_counts`, summaries report node, edge, authority-category, source-status,
source-partition, source-currentness, applicability-status, and readiness-blocker counts,
`phase-eval` includes optional `nepa_3d_source_set_graph` and `nepa_3d_review_graph` phases when
the graph artifacts exist, and
`config/promotion_suite_v1.json` requires source-set plus V1 review graph validation/summary
artifacts for current promotion.

Latest local signals:

- source-set graph export: `62/62` validation checks, `failure_category_counts={}`, `1,470` nodes,
  and `2,648` edges;
- V1 review graph export: `76/76` validation checks, `failure_category_counts={}`, `1,996` nodes,
  and `3,550` edges;
- V1 review-bound `phase-eval`: `20/20` phases passed with `reviewer_ready=true`;
- non-strict `promotion-suite`: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `expansion_artifacts_ready=false`, `26/26` required current-promotion
  results passed, `failure_category_counts={}`, and
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`;
- strict expansion `promotion-suite`: expected command failure with `current_promotion_ready=true`,
  `promotion_ready=false`, `expansion_ready=false`, `26/26` required current-promotion results
  passed, `open_expansion_artifact_count=5`, and `open_expansion_slot_count=1`.

Next implementation target: no additional NEPA 3D Milestone 7 pass is selected yet. Reasonable next
slices are a deeper graph failure-fixture pass, the Milestone 8 operating runbook/demo closeout, or
the deferred Beaverhead-Deerlodge component-inventory build if the user chooses to deepen Region 1
forest-plan readiness first.

## Current Architecture Hardening State

The agentic coding architecture sequence has implemented the architecture map, contract, first
fitness gate, rule-pack ownership split, CLI lane split, hotspot report, and ADR set through
Milestone 6. The operative architecture references are:

- `docs/ARCHITECTURE.md`
- `docs/architecture_contract.toml`
- `docs/HOTSPOT_REPORT_2026_05_04.md`
- `docs/adr/0001-architecture-fitness-gates.md`
- `docs/adr/0002-applicability-before-compliance.md`
- `docs/adr/0003-rule-pack-ownership.md`
- `docs/adr/0004-untrusted-source-content.md`
- `docs/adr/0005-architecture-gates-in-milestone-closeout.md`

### Compliance Review Hotspot Reduction

Sequence 6 is implemented for the compliance-review hotspot split. The new
`src/usfs_r1_ea_sources/compliance_review_eval.py` module owns the deterministic
compliance-review eval harness only: eval case loading and validation, fixture package
materialization, eval review invocation, case scoring, mismatch metrics, failure taxonomy, and
reproduction metadata. Sequence 5 kept
`src/usfs_r1_ea_sources/compliance_findings.py` as the owner for compliance finding construction
only: authority-family inventory indexing, authority-family ID resolution for generated/base rules,
source-claim evidence compaction, citation-label extraction, and claim-type assignment. Sequence 4
kept
`src/usfs_r1_ea_sources/compliance_finding_graph.py` as the owner for finding-graph artifact assembly
only: compliance review/rule/finding nodes, source-library evidence nodes, source-claim nodes,
package-evidence and package-gap nodes, graph edges, and the Forest Plan review/component-eval graph
projection. Sequence 3 kept
`src/usfs_r1_ea_sources/compliance_authority_integration.py` as the owner for authority-integration
artifact assembly only: authority-family provenance, non-applicable authority appendix JSON and
Markdown, authority reviewer-resolution report, deterministic litigation-risk summary, and the
private row/risk helpers needed to assemble those artifacts. Sequence 2 kept
`src/usfs_r1_ea_sources/compliance_validation.py` as the owner for compliance validation and
review-summary assembly helpers, and Sequence 1 kept
`src/usfs_r1_ea_sources/compliance_inputs.py` as the owner for compliance-review input and
identity/gate-context helpers.

The current post-split line-count baseline is `compliance_review.py` `398`,
`compliance_review_eval.py` `954`, `compliance_findings.py` `217`,
`compliance_finding_graph.py` `340`, `compliance_authority_integration.py` `493`,
`compliance_validation.py` `762`, `compliance_inputs.py` `561`, and
`compliance_outputs.py` `1,019`; the deferred hotspot baselines remain
`nepa_knowledge_graph_export.py` `3,391`, `forest_plan_components.py` `3,302`,
`ea_consistency_decision_support.py` `3,090`, and `viewer/nepa-3d/app.js` `2,202`.

Sequence 6 does not intentionally change finding selection, compliance status decisions, generated
rule-pack semantics, Forest Plan component evaluation, matrix/PDF output, finding graph output,
eval scoring semantics, CLI flags, or generated artifact schemas. No Sequence 7 split is selected
yet; rerank remaining hotspots before continuing beyond this eval-harness boundary.

Sequence 6 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 5 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 4 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 3 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 2 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 1 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 0 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`. Existing untracked root-level East Crazies manual draft
exports and `docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf` remain non-canonical and were
left untouched.

## Current Applicability-First State

The current active implementation lane is the post-V1 applicability-first review architecture in
`docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md`. The V1 EA gate remains promoted for the Custer
Gallatin East Crazy proving package, but new work has moved into a pre-review applicability
pipeline that separates authority applicability from compliance findings.

Current completed applicability milestones:

- Milestone 1 schema plan: artifact contracts for package fact graph, retrieval trace, graph trace,
  search coverage certificates, applicability decisions, provenance, validation/adjudication, and
  generated rule pack are documented in `docs/OUTPUT_SCHEMAS.md`.
- Milestone 2 authority universe: `applicability-authority-universe` writes
  `authority_universe_snapshot.json` with rule-template and Forest Plan component candidates,
  source evidence requirements, package/source filters, retrieval contracts, graph-expansion
  contracts, dependency/exception/supersession fields, and search coverage requirements.
- Milestone 3 package context: `applicability-context-build` reads the existing EA package cache and
  writes `package_fact_graph.json`, `package_applicability_context.json`, and
  `package_fact_graph_validation.json` with typed, span-bound package facts and uncertainty records.
- Milestone 4 retrieval/graph traces: `applicability-retrieve` writes
  `applicability_retrieval_trace.jsonl`, `applicability_graph_trace.jsonl`, and
  `applicability_retrieval_graph_diagnostics.json` with replayable per-candidate retrieval rows,
  RRF fused result rows, bounded graph paths, and diagnostics.
- Milestone 5 deterministic decisions: `applicability-determine` writes
  `applicability_decisions.jsonl`, `applicable_authorities.json`,
  `non_applicable_authorities.json`, `search_coverage_certificates.json`,
  `applicability_provenance.json`, and `applicability_report.md` without producing compliance
  findings or a generated rule pack.
- Milestone 6 validation/adjudication: `applicability-validate` writes
  `applicability_validation.json` and fails closed on missing, duplicated, stale, unsupported, or
  unresolved decisions. `applicability-adjudication-template`,
  `applicability-adjudication-eval`, and `applicability-adjudication-apply` provide replayable
  machine-readable adjudication; apply rewrites the decision ledger and applicable/non-applicable
  partitions with `human_adjudication` bases and updates provenance. The gap-close pass hardened
  validation around package fact-graph validation status, contradiction/adjudication handling,
  adjudication eval replayability, partition/coverage freshness, and provenance entity hashes.
- Milestone 7 generated rule pack: `applicability-generate-rule-pack` writes
  `generated_rule_pack.json` and `generated_rule_pack_validation.json` only from a passing and
  current applicability validation. Generated packs contain validated applicable authorities only
  and carry explicit base/generated rule IDs, decision, retrieval, graph, source-record,
  source-claim, package-section, Forest Plan, per-rule artifact hashes, freshness, and provenance
  metadata. `--validate-only` requires a previously recorded generated-pack hash and detects manual
  edits, stale applicability validation, and upstream artifact drift.
- Milestone 8 compliance-review gate: reviewer-ready `compliance-review` now requires a generated
  applicability rule pack plus passing applicability/generated-pack validation, matching package
  manifest, package-chunk, source-set, and provenance hashes, a valid
  `non_applicable_authorities.json`, and search coverage for non-applicable authorities. Generated
  validation must explicitly record `generated_rule_pack_ready=true`. The base rule pack can still
  be run with `--allow-base-rule-pack-review`, but that diagnostic output is not reviewer-ready and
  cannot make compliance-gold eval promotion-ready.
- Milestone 9 applicability eval gates: `applicability-eval` runs deterministic seed packages
  through the full applicability sequence and checks expected statuses, package facts,
  retrieval/graph traces, source-record/document-role/package-section alignment, non-applicable
  coverage, required artifact presence, and generated-rule-pack identity/hash alignment.
  `applicability-gold-eval` requires adjudicated positive, mixed, and negative profiles before
  promotion. `phase-eval --review-id/--review-dir` now includes authority-universe, package-fact
  graph, applicability retrieval trace, applicability graph trace, applicability determination,
  applicability validation, and generated-rule-pack phases before compliance review. The
  gap-closure pass added regression coverage for missing non-applicable artifacts, graph trace gaps,
  generated-pack hash edits, source/document-role/package-section mismatches, and stale
  file-backed applicability validation hashes.

Latest applicability and evidence-arbitration commits:

- `8018648` - Harden applicability authority universe
- `f5a3db1` - Close authority universe contract gaps
- `0f4a851` - Add applicability package fact graph
- `4656283` - Close package fact graph gaps
- `0f30761` - Add applicability retrieval traces
- `e9e3abe` - Close applicability retrieval graph gaps
- `08b1aae` - Add deterministic applicability decisions
- `aa0c1da` - Close applicability decision gaps
- `6bed025` - Add applicability validation adjudication gate
- `a60c382` - Close applicability validation gate gaps
- `99ae407` - Add applicability generated rule pack
- `53061f6` - Close generated rule pack gate gaps
- `75672da` - Gate compliance review on generated rule pack
- `69e83bb` - Implement authority applicability eval coverage
- `0d48d4b` - Close authority applicability milestone gaps
- `992a079` - Implement authority report integration
- `9a9d256` - Implement evidence arbitration diagnostics
- `a3c967a` - Implement evidence strength model
- `8f8b15d` - Close evidence arbitration diagnostic gaps
- `cf325ba` - Implement trigger arbitration predicate
- `34fca93` - Implement ECID arbitration replay
- `f304e2e` - Add arbitration eval reporting coverage

Important current behavior:

- Applicability artifacts are produced before compliance review and do not contain `pass`, `gap`, or
  `uncertain` compliance findings.
- Trigger arbitration now distinguishes decisive strong package evidence from weak auxiliary
  evidence. All-weak trigger evidence and unresolved positive/negative conflicts are still recorded
  as `needs_adjudication`.
- Evidence-arbitration Milestones 1 and 2 are implemented as behavior-preserving diagnostics:
  decisions carry `arbitration_summary`, evidence spans carry structured `evidence_strength`, and
  reports show weak/auxiliary/conflicting trigger-group diagnostics without changing final
  applicability status outcomes. The gap-close pass added structured weak-signal reason notes,
  broader no-action/no-change background classification, negative-phrase preservation, and package
  graph assertions for fact/context/uncertainty evidence-strength propagation.
- Evidence-arbitration Milestone 3 is implemented as active trigger arbitration. Strong,
  rule-contract-sufficient positive trigger groups can carry `applicable` status with weak
  auxiliary evidence retained in notes and diagnostics. All-weak positive evidence and
  positive-plus-negative conflicts remain `needs_adjudication`.
- Not-applicable decisions cite search coverage certificates.
- Validation now fails if a final contradictory decision lacks human adjudication, if a
  human-adjudicated decision cannot be replayed from a passing adjudication eval, if
  `package_fact_graph_validation.json` is stale or failed, or if partition/coverage/provenance
  hashes drift from current applicability artifacts.
- Milestone 5 gap closure added raw package-chunk checks for explicit negative evidence,
  source-index hash requirements for sufficient coverage, retained source-library evidence spans on
  non-applicable decisions, local-evidence trigger-group matching, and package manifest/chunk
  provenance entities.
- `compliance-review` no longer runs reviewer-ready reviews directly against the base rule pack.
  Generated-rule-pack review evaluates generated applicable rules only; non-applicable authorities
  stay in `non_applicable_authorities.json`, which the compliance matrix links as the source of
  truth.
- `compliance-review-eval` may still score deterministic compliance fixtures with the base rule
  pack, but those runs are diagnostic and default to non-reviewer-ready validation expectations.
  `compliance-gold-eval` now emits `promotion_ready=true` only for reviewer-ready generated
  applicability rule packs. Applicability-quality evals now exist so generated review success is no
  longer the only proxy for applicability correctness.

Latest verification for the current applicability/evidence-arbitration lane:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py tests/test_promotion_suite.py tests/test_applicability_decisions.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json --eval-file config/applicability_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gold-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json --gold-file config/applicability_gold_eval_v0.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/applicability_eval_seed.json /tmp/applicability_eval_seed.validated.json
python -m json.tool config/applicability_gold_eval_v0.json /tmp/applicability_gold_eval_v0.validated.json
python -m json.tool config/promotion_suite_v1.json /tmp/promotion_suite_v1.validated.json
git diff --check
```

Verified results from the latest Milestone 5 arbitration coverage pass:

- Focused applicability/promotion regression suite: `42 passed`
- Architecture contract: `5 passed`
- `applicability-eval`: passed `9/9` seed cases; arbitration status/effect match rates were `1.0`
- `applicability-gold-eval`: passed `5/5` adjudicated cases and emitted `promotion_ready=true`
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `16/16` phases with
  `applicability_arbitration_summary` emitted
- `promotion-suite`: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`; expansion blockers remain `adjudication_needed` and
  `package_fixture_missing`
- The current V1 applicability artifact family remains reviewer-ready with `377` candidates, `37`
  applicable authorities, `340` non-applicable authorities, no unresolved/adjudication decisions,
  and `generated_rule_pack_ready=true`.
- Ruff, compileall, JSON validation, and `git diff --check`: passed

Latest evidence-arbitration Milestone 3 closeout verification:

- `tests/test_applicability_decisions.py`: `24 passed`
- `tests/test_applicability_eval.py`: `11 passed`
- `tests/test_architecture_contract.py`: `5 passed`
- `tests/test_package_fact_graph.py`: `4 passed`
- `ruff check src tests`: passed
- `python -m compileall src`: passed
- `git diff --check`: passed

Latest evidence-arbitration Milestone 4 closeout verification:

- `applicability-determine`: replayed `392` ECID candidate authorities to `43` applicable, `346`
  non-applicable, and `3` `needs_adjudication`.
- `applicability-validate`: expected reviewer-readiness failure; failure categories were limited to
  `unresolved_authority` for the three positive/negative authority conflicts.
- `applicability-adjudication-template`: emitted the three-item worklist for cultural-resource/SHPO,
  minerals/energy, and species-supporting authorities.
- `promotion-suite`: kept current promotion ready and expansion not ready; expansion blockers are
  `adjudication_needed` and `package_fixture_missing`.
- `tests/test_applicability_decisions.py`: `25 passed`
- `tests/test_promotion_suite.py`: `6 passed`
- `tests/test_applicability_eval.py`: `11 passed`
- `tests/test_architecture_contract.py`: `5 passed`
- `ruff check src tests`, `python -m compileall src`, JSON validation, and `git diff --check`:
  passed.

Latest evidence-arbitration Milestone 5 closeout verification:

- `applicability-eval`: passed `9/9` seed cases with arbitration status/effect match rates of
  `1.0`; aggregate arbitration counts include `1` applicable-with-weak-auxiliary, `2` weak-only
  needs-adjudication, `1` insufficient-strong-trigger needs-adjudication, and `1`
  positive/negative-conflict needs-adjudication.
- `applicability-gold-eval`: passed `5/5` cases with `promotion_ready=true` and a passing
  `gold_eval_cases_have_arbitration_expectations` check.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `16/16` phases and emitted
  `applicability_arbitration_summary`.
- `promotion-suite`: kept current promotion ready and expansion not ready; expansion blockers remain
  `adjudication_needed` and `package_fixture_missing`.
- `tests/test_applicability_decisions.py`: `25 passed`
- `tests/test_applicability_eval.py`: `11 passed`
- `tests/test_promotion_suite.py`: `6 passed`
- `tests/test_architecture_contract.py`: `5 passed`
- `ruff check src tests`, `python -m compileall src`, JSON validation, and `git diff --check`:
  passed.

Latest post-V1 real-package expansion Sequence 0 baseline lock:

- `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` Sequence 0 is complete. This pass did
  not adjudicate ECID, add a third package fixture, or change the promotion manifest.
- Non-strict promotion-suite run wrote
  `source_library/reviews/promotion_suite/sequence0-baseline-nonstrict/promotion_suite_results.json`
  and reported `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `failure_category_counts={}`,
  `expansion_failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`,
  and `open_expansion_slot_count=2`.
- Strict promotion-suite run wrote
  `source_library/reviews/promotion_suite/sequence0-baseline-strict/promotion_suite_results.json`
  and failed as expected with `current_promotion_ready=true`, `promotion_ready=false`,
  `expansion_ready=false`,
  `failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`,
  `expansion_failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`,
  and `open_expansion_slot_count=2`.
- At Sequence 0, the ECID adjudication template/worklist at
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/` had three pending
  `needs_adjudication` items: `cultural_resource_protection_and_state_shpo_sources`
  (`decision_id=6f349222ecfa557b7d163d68`), `minerals_energy_authorities`
  (`decision_id=add0df8c2b513d6068b4edcc`), and
  `species_supporting_sources_and_overlays` (`decision_id=58df28f23d0b2222f32eb687`).

Latest post-V1 real-package expansion Sequence 1 adjudication closure:

- `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` Sequence 1 is complete. The ECID
  adjudication template was completed for the three pending authority-family conflicts and left in
  ignored `source_library/` evidence artifacts.
- The three adjudicated families are now `human_applicable`:
  `cultural_resource_protection_and_state_shpo_sources`,
  `minerals_energy_authorities`, and `species_supporting_sources_and_overlays`.
- `applicability-adjudication-eval` passed with `3` resolved adjudications, `0` pending
  adjudications, and `failure_category_counts={}`.
- `applicability-adjudication-apply` passed with `applied_item_count=3`,
  `remaining_unresolved_authority_count=0`, and applied decision-ledger hash
  `207f2c17c8e13708dc46b6b50581183f5ea6af523cc3aeb76d585557fcfb77cd`.
- `applicability-validate` passed with `46` applicable authorities, `346` non-applicable
  authorities, `0` unresolved, `0` `needs_adjudication`, `generated_rule_pack_ready=true`,
  `reviewer_ready=true`, and `failure_category_counts={}`.
- Sequence 1 did not generate the ECID rule pack, run compliance review, run phase eval, update the
  promotion manifest, or add the missing third real-package fixture. Sequence 2 has since completed
  the artifact-generation and promotion-manifest pass described below.

Latest post-V1 real-package expansion Sequence 2B/3 status:

- `applicability-generate-rule-pack` passed for
  `region1-expansion-ecid-preliminary-ea`, producing a generated ECID rule pack with `46` rules and
  `generated_rule_pack_ready=true`.
- `compliance-review` against the generated ECID rule pack wrote
  `compliance_review.json`, `compliance_validation.json`, `compliance_matrix.json/.md/.pdf`,
  authority-family provenance, non-applicable authority appendix, authority reviewer-resolution,
  litigation-risk, rule-claim, and finding-graph artifacts. Sequence 2A closed the source-claim
  blocker: `rule_claim_gap_count=0`, `rule_claim_link_count=211`, and
  `rule_claim_rules_without_links=[]`. Sequence 2B closed the Forest Plan component blocker:
  compliance review now reports `reviewer_ready=true` and validation passes.
- ECID Forest Plan component status: `29` applicable standards, `7` applied standards, `158`
  reviewer-resolution rows, all queued as `missing_package_evidence`; Sequence 2B adjudication
  eval resolves all `158` as true EA package-evidence omissions with `0` system misses.
- `phase-eval --review-id region1-expansion-ecid-preliminary-ea` now writes a review-scoped copy at
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/phase_eval_results.json`; the ECID
  Sequence 2B run passes with `16/16` phases and `reviewer_ready=true`.
- The shared source-set phase-eval artifact was restored by rerunning
  `phase-eval --review-id v1-cg-ecid-compliance-review`; the later NEPA 3D graph-gate pass now has
  that promoted V1 review artifact at `19/19`.
- `forest-plan-component-adjudication-template` generated a `158`-item ECID worklist at
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/forest_plan_component_adjudication_template.json`
  and `.md`.
- `config/promotion_suite_v1.json` now includes ECID and South Plateau `required_for_expansion`
  artifact checks and treats expansion readiness as both slot readiness and required expansion
  artifact readiness. ECID remains `ready=true`; South Plateau is `ready=false` with
  `forest_plan_reviewer_not_ready` until its declared Custer Gallatin forest-plan context becomes
  reviewer-ready. Ready-slot `expected_gate_artifacts` cover the matching review-case
  `required_for_expansion` artifact IDs, and declared forest-profile slots must include
  `compliance_review`, `forest_plan_context_summary`, and `phase_eval` gate contracts.
- Historical non-strict promotion suite after Sequence 7 reported `current_promotion_ready=true`,
  `promotion_ready=true`, `expansion_ready=false`, `expansion_artifacts_ready=false`,
  `failure_category_counts={}`, `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 3}`,
  `open_expansion_artifact_count=2`, and `open_expansion_slot_count=1`; the current closeout
  signal after final QA and South Plateau context updates is `26/26` current-promotion results and
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`.

Next implementation target:

Sequence 7 in `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` is complete. The declared
ECID preliminary-EA and South Plateau expansion set no longer reports strict expansion ready while
South Plateau forest-plan context is ambiguous. The older lane notes below are retained for
continuity, but they are not the current next pass unless the user redirects.

Sequence 2B alignment/gap close note: strict and non-strict promotion-suite evidence were kept
separate, and non-strict was rerun last so the default suite output remains the current-promotion
signal. The ECID implementation reused the existing package/cache, turned each of the `158` rows
into an actionable QA/QC disposition, preserved compact component/source refs on every resolved
item, and preserved the missing evidence as visible gaps rather than converting the review into a
legal conclusion.

- `docs/EA_CONSISTENCY_DECISION_SUPPORT_MILESTONE_PLAN.md`: close the gap between reviewer-ready
  East Crazies evidence artifacts and a single Responsible Official-facing EA consistency
  decision-support document. This lane must generate a report from audited review artifacts,
  not from root-level manual draft prose, and must preserve the applicable/non-applicable authority
  boundary, Forest Plan component coverage, applicable-standard coverage, residual risk register,
  and implementation confirmation checklist. Sequence 0 preflight is complete in
  `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md` and the pass artifacts below. Sequences 1
  through 5 are complete; the EA consistency decision-support milestone has no remaining planned
  sequence. Future work should be a new milestone or a targeted copy-review pass, not a continuation
  of this implementation lane.
  - Sequence 0 pass 1 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_1_WORKSPACE_BOUNDARY.md`: tracked
    worktree status was clean at pass start, root-level `East_Crazies_*` exports are quarantined as
    non-canonical manual draft comparison material, and `source_library/` remains ignored. The next
    preflight pass is artifact freshness and hash baseline.
  - Sequence 0 pass 2 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_2_ARTIFACT_FRESHNESS.md`: all required
    review artifacts exist and parse, validation-owned artifact hashes match current files, the
    review/source-set/package boundary agrees, and the Plan Consistency Table hash baseline records
    both raw-file and normalized-text hash shapes. The next preflight pass is current gate replay.
  - Sequence 0 pass 3 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_3_CURRENT_GATE_REPLAY.md`: `phase-eval`
    passed `16/16` with `reviewer_ready=true`, `promotion-suite` reported
    `current_promotion_ready=true` and `promotion_ready=true`, and broader expansion blockers
    remain separated from the current East Crazies promotion gate. The next preflight pass is Forest
    Plan consistency baseline.
  - Sequence 0 pass 4 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_4_FOREST_PLAN_CONSISTENCY_BASELINE.md`:
    `EA-PACKAGE-042` is present once as extracted Plan Consistency Table package evidence,
    generated Forest Plan artifacts remain canonical, component findings report `329` findings with
    `79` supported/applicable and `250` not applicable, applicable-standard coverage reports `58`
    standards with `12/12` applied, Custer Gallatin context remains reviewer-ready, and manual
    root-level East Crazies prose remains quarantined. The next preflight pass is Authority Universe
    Boundary.
  - Sequence 0 pass 5 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_5_AUTHORITY_UNIVERSE_BOUNDARY.md`:
    applicable and non-applicable authority partitions are disjoint and cover all `377` candidates,
    with `37` applicable authorities, `340` non-applicable authorities, `340` search coverage
    certificates, exact non-applicable appendix alignment, generated-rule-pack validation proving
    generated rules derive only from applicable authorities, and the compliance matrix linking to
    non-applicable artifacts instead of double-counting them as findings. The next preflight pass is
    Residual Risk And Implementation Confirmation Source Mapping.
  - Sequence 0 pass 6 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_6_RESIDUAL_RISK_IMPLEMENTATION_SOURCE_MAPPING.md`:
    residual-risk rows are mapped to `litigation_risk_summary.json`,
    `authority_reviewer_resolution_report.json`, compliance limitation fields, Forest Plan
    applicable-standard limitations, and Forest Plan reviewer-resolution artifacts; the current
    risk state has `340` deterministic informational non-applicable-boundary flags, `0` legal
    conclusion flags, `0` open authority-resolution items, `0` open Forest Plan reviewer-resolution
    items, no compliance limitations, and no applicable-standard failure reasons. Every required
    implementation-confirmation checklist item has current generated evidence selectors plus a
    planned tracked configuration owner in `config/ea_consistency_decision_support_v1.json` for
    Sequence 1. The next preflight pass is CLI, Module, And Renderer Ownership.
  - Sequence 0 pass 7 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_7_CLI_MODULE_RENDERER_OWNERSHIP.md`:
    the full milestone implementation surface is now fixed as the `ea-consistency-document` CLI
    command, a new `cli_decision_support.py` command lane, canonical module
    `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`, a new architecture-contract
    `decision_support` layer and command group when code is introduced, generated artifacts under
    `source_library/reviews/<review_id>/decision_support/`, schema documentation in
    `docs/OUTPUT_SCHEMAS.md`, config ownership in `config/ea_consistency_decision_support_v1.json`,
    and focused tests in `tests/test_ea_consistency_decision_support.py`, `tests/test_cli.py`, and
    `tests/test_architecture_contract.py`. The renderer path should follow the existing
    compliance-output JSON-to-Markdown/PDF pattern without importing private helpers or adding
    system PDF dependencies. The next preflight pass is Fixture And Regression Contract.
  - Sequence 0 pass 8 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_8_FIXTURE_REGRESSION_CONTRACT.md`:
    fixture/regression expectations are fixed for required report sections, current count fields,
    required input hash fields, representative applicable authority row (`flpma_section_206_land_exchange`),
    representative non-applicable authority row (`directives_notice_comment_36cfr_216`) with search
    coverage, representative Forest Plan row (`FW-STD-RMZ-01`), all `12` applicable standards, and
    fail-closed categories for missing, stale, or mismatched inputs, count drift, missing
    non-applicable summaries, unresolved implementation selectors, residual-risk legal conclusions,
    manual-draft dependency, and invalid or missing PDF output. Sequence 0 preflight is complete
    with `go`; the next boundary is Sequence 1 Report Contract And Fixtures.
  - Sequence 1 is complete: `docs/OUTPUT_SCHEMAS.md` now documents the
    `ea-consistency-decision-support-report-v1` artifact family; tracked config
    `config/ea_consistency_decision_support_v1.json` owns section order, grouping, caveat wording,
    implementation-confirmation selectors, residual-risk rules, and report-quality eval
    expectations; `config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json`
    locks the current East Crazies sections/counts/hashes/sample rows/applicable standards/failure
    categories; `tests/fixtures/decision_support/minimal_decision_support_report.json` proves the
    synthetic schema boundary; and `tests/test_ea_consistency_decision_support.py` validates
    schema/config/fixture contracts including row-level `trace_ids`, `source_selectors`,
    false-positive synthesis claims, and false-negative synthesis omissions.
  - Sequence 2 is complete: `src/usfs_r1_ea_sources/ea_consistency_decision_support.py` implements
    the deterministic report generator, `src/usfs_r1_ea_sources/cli_decision_support.py` registers
    `ea-consistency-document`, and `docs/architecture_contract.toml` now owns the
    `decision_support` layer, command group, and generated artifact family. The generator validates
    required audited inputs, compares the Sequence 1 hash/count contract, fails closed on missing,
    stale, hash-mismatched, non-reviewer-ready, unresolved-selector, missing-evidence, or
    legal-conclusion conditions, and writes canonical JSON plus Markdown, PDF, and manifest outputs
    under `source_library/reviews/<review_id>/decision_support/`. A local run for
    `v1-cg-ecid-compliance-review` passed and wrote the ignored generated report family with `37`
    applicable authority findings, `340` non-applicable authorities, `329` Forest Plan component
    rows, `12/12` applicable standards applied, `0` open authority/Forest Plan resolution items, and
    a valid `%PDF-` PDF header. Sequence 3 closed out that first real report output; Sequence 4 now
    owns gate integration.
  - Sequence 3 is complete: the 2026-05-06 local closeout run generated the ignored East Crazies
    decision-support family under
    `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/`:
    `ea_consistency_decision_support.json`, `.md`, `.pdf`, and `_manifest.json`. The generated
    report validation passed with `37` applicable authority findings rendered as `pass`, `340`
    non-applicable authorities summarized with search coverage, `329` Forest Plan component rows,
    all `12/12` applicable Forest Plan standards carrying package and plan evidence, `9`
    implementation-confirmation rows with evidence, `3` residual-risk notes, `0` legal-conclusion
    risk flags, and a valid `%PDF-` PDF header. No `source_library/` outputs were staged.
  - Sequence 4 is complete: `ea-consistency-document --validate-only` validates the existing
    generated report family without rewriting it; `phase-eval --review-id
    v1-cg-ecid-compliance-review` now includes the `decision_support_report` phase and passed
    `17/17` phases with `reviewer_ready=true`; `promotion-suite` requires the decision-support
    report JSON, manifest, and PDF for current promotion and reports `current_promotion_ready=true`,
    `promotion_ready=true`, and `expansion_ready=false`. The validator fails closed on stale input
    hashes, missing sections, missing non-applicable summaries, missing applicable standards,
    invalid PDF output, manual-draft dependency, unresolved implementation confirmations, and
    residual-risk legal conclusions.
  - Sequence 5 is complete: the Markdown/PDF renderer now front-loads a "How To Use This Document"
    note, bottom-line reviewer-ready status, authority categories/status counts, Forest Plan basis,
    applicable-standard coverage, non-applicable authority boundary, implementation confirmations,
    residual risks, validation status, and concise table summaries before the long authority and
    Forest Plan evidence sections. Implementation-confirmation rows show constrained
    decision-support wording plus evidence selectors; residual-risk rows preserve source artifact
    and selector pointers; and the caveat states the document supports review but does not replace
    responsible official, line officer, counsel, or specialist judgment. The generated
    `source_library/` report family remains ignored and should not be staged unless policy changes.
  - Post-sequence gap close is complete: validation now checks the Markdown/PDF supervisor rendering
    contract directly. Missing front matter, review snapshot, table summaries, key counts, required
    sections, source pointers, or Markdown section ordering fails as
    `false_negative_synthesis_omission` with `decision_support_markdown.*` or
    `decision_support_pdf.*` source selectors. This closes the gap against the
    thought-leader review's report-quality eval guidance without adding a new sequence.
- `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md` Milestone 10: the ECID three-item
  applicability adjudication worklist, generated-rule-pack/artifact-check pass, source-claim gap
  closure, Forest Plan component adjudication replay, and third package fixture selection are
  complete. The selected South Plateau run is now complete through applicability validation,
  generated rule-pack validation, compliance review, review-scoped phase eval, and Sequence 7
  strict-expansion fail-closed hardening.
- `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md`: focused closure plan for resolving
  `expansion_ready=false`; complete through Sequence 7 for the declared expansion set, with South
  Plateau intentionally blocked on `forest_plan_reviewer_not_ready`.
- `docs/SOUTH_PLATEAU_FOREST_PLAN_CONTEXT_MILESTONE_PLAN.md`: active follow-up plan for resolving
  the remaining South Plateau strict-expansion blocker without weakening the declared-profile,
  compliance-review, phase-eval, or promotion-suite gates.
- `docs/NEPA_3D_KNOWLEDGE_GRAPH_MILESTONE_PLAN.md`: build a source-set and review-specific
  knowledge graph export plus local 3D viewer for all USDA/Forest Service Region 1 EA authority
  families, applicability decisions, evidence paths, supersession/currentness states, and readiness
  blockers. This lane must start as a visualization/export layer over existing audited artifacts,
  not as a separate legal knowledge base.
- NEPA 3D Milestone 2A is implemented. `config/source_partition_contract_nepa_3d_v1.json` and
  `source_partitions.py` define `active_review_corpus`,
  `currentness_supersession_archive`, and `candidate_blocked_source`; future `catalog-build`
  outputs carry `source_partition` and `source_partition_basis`; and `authority-currentness` now
  reports catalog partitions, per-family graph roles, and fail-closed checks for non-current active
  sources, reserved/superseded active authority, superseded-family graph relationships, and
  collapsed FSH 1909.15 handbook records. The gap-closure pass also validates the contract's
  required partitions, active/non-active eligibility boundary, non-active graph relationship limits,
  reserved `36 CFR part 220` archive boundary, and scoped workbook/source-delta plan. The live
  currentness gate passed with `189` active review-corpus records and `1` candidate/blocked source.
- NEPA 3D Milestone 1 is implemented. `config/nepa_3d_graph_contract_v1.json`,
  `nepa_3d_graph_contract.py`, `docs/OUTPUT_SCHEMAS.md`, and
  `tests/fixtures/nepa_3d_graph/` now define and validate the source-set/review graph export schema,
  node and edge types, display states, review-readiness states, required per-node provenance fields,
  edge endpoint compatibility, required lens metadata, currentness metadata, validation shape, and
  readiness blockers before exporter implementation.
- NEPA 3D Milestone 3 is implemented. `nepa_knowledge_graph_export.py` and the
  `nepa-knowledge-graph-export` CLI command build the source-set graph from catalog graph seeds,
  authority inventory/currentness, evidence graph inputs, source claims, rule-claim links, the base
  rule pack, authority-family templates, forest-plan profiles, and forest-plan component inventory.
  The refreshed `source-set-ba8d0feae79501b8` export passed `62` validation checks with `1,470`
  nodes, `2,648` edges, all `35` authority families, all `190` catalog source records, all `48` base
  rules, all `19` authority-family templates, `211` rule-claim links, and `329` forest-plan
  components.
- NEPA 3D Milestone 4 is implemented. `nepa-knowledge-graph-export --review-id` writes the
  review-specific graph under `source_library/reviews/<review_id>/knowledge_graph/` from existing
  applicability-first and compliance artifacts. The refreshed `v1-cg-ecid-compliance-review`
  overlay passed `76` validation checks with `1,996` nodes, `3,550` edges, `377` candidate
  authorities/decisions, `37` generated rules and compliance findings, and `340` non-applicable
  authorities with search coverage. The gap-close checks now also require hashed review artifact
  inputs and resolving search-coverage, retrieval-trace, and graph-trace references.
- NEPA 3D Milestone 5 is implemented. `config/region1_forest_plan_readiness_nepa_3d_v1.json`
  tracks `10` Region 1 forest/grassland profiles, `3` field-directive requirements, and `5`
  overlay requirement groups. `config/forest_plan_profiles.json` now contains the first added
  Beaverhead-Deerlodge profile contract with catalog-confirmed planning page/LMP source rows,
  positive and hard-negative applicability fixture contracts, and a component-inventory blocker
  before graph promotion. The source-set graph passed `62` validation checks with `1,470` nodes and
  `2,648` edges, `1` graph-ready profile, `9` broader Region 1 profiles blocked from completeness
  claims, and graph-visible field-directive/overlay requirement nodes linked to catalog sources.
- NEPA 3D Milestone 6 is implemented. `viewer/nepa-3d/` is a checked-in static viewer over the
  normalized graph export. It uses `viewer/nepa-3d/manifest.json` as a fallback manifest, resolves
  the live source-set default from `source_library/catalog/source_set_manifest.json`, prefers that
  catalog source set when a graph export exists, otherwise falls back to the newest graph-capable
  source set under `source_library/derived/`, and only offers review overlays whose graph summaries
  match the resolved source set. A fresh load and Reset demo now return to the full validated
  source-set corpus graph for that resolved dataset; demo scenes narrow from that full-corpus
  start instead of opening in a review-specific applicability view. It still uses Three.js plus
  `3d-force-graph`, exposes the required selectors/search/filters/layout controls,
  and keeps readiness tied to graph validation rather than layout. Static tests now lock the pinned
  runtime URLs, fallback relative graph paths, runtime dataset discovery hooks, and `node_id`/edge
  endpoint mapping; local browser verification covered desktop source-set, desktop review overlay,
  and mobile graph canvas screenshots with nonblank graph-root pixel checks.
- NEPA 3D Milestone 6 dropdown gap closure is implemented in the isolated worktree branch
  `codex/nepa-3d-dropdown-gaps`. The viewer now separates authority category and authority family,
  labels status/readiness and currentness/partition filters more accurately, splits node/edge type
  from evidence/basis values, reads forest-unit filters from exported `forest_code` values, adds
  graph-export counts plus grounding metadata to lens and filter options, adds a Clear filters
  action, and treats dropdown/search selections as context seeds so populated options no longer
  blank the graph. Live browser sweep on the isolated viewer covered all populated source-set and
  review-overlay lens/filter dropdown selections with `0` zero-node selections; some selections
  still show nodes without edges when the active lens has no matching edge path, and the status line
  now tells reviewers to try All validated graph data or clear filters.
- NEPA 3D Milestone 6 demo-mode closeout is implemented in the same isolated worktree branch. The
  viewer defaults to `v1-cg-ecid-compliance-review`, adds scene buttons above Lens, keeps the
  original dropdowns under Advanced filters, adds Reset demo, adds a right-side Capability shown
  panel with rendered graph counts and proof labels, and derives the evidence-path spotlight from
  actual graph edges so source record, artifact, chunk, evidence span, source claim, rule, decision,
  generated rule, and compliance finding steps are clickable rather than hard-coded.
- NEPA 3D graph legibility closeout adds scene labels and progressive node labels to the graph
  surface. Labels are generated from rendered graph nodes as Three.js sprites, show scene/anchor
  labels while zoomed out, reveal focus labels at mid zoom, and reveal additional node labels when
  zoomed closer. This is a visual legibility layer only; it does not alter graph validation,
  readiness, or source evidence.
- NEPA 3D service capabilities brief closeout adds a generated 3-page brief at
  `docs/capabilities/nepa_3d_capabilities_brief.pdf` with a matching HTML source and high-resolution
  graph figures under `docs/capabilities/assets/`. The brief is built by
  `tools/build_nepa_3d_capabilities_brief.mjs` from current catalog, source-set graph,
  phase-eval, and promotion-suite artifacts. The current version is a reusable system-level brief
  organized around the Region 1 knowledge-system message: fragmented source, authority, evidence,
  and forest-plan data is structured into a relational graph for defensible, efficient land exchange
  execution. NEPA review is the V1 function, and the same graph foundation can expand to additional
  workflows while showcasing distinct NEPA, USDA regulation, source-evidence, and forest-plan layers
  without named project examples.
- NEPA 3D Milestone 7 initial graph validation and promotion gates are implemented for the current
  source-set and V1 review overlay. A follow-up pass should either deepen graph-specific failure
  fixtures, move to Milestone 8 operating runbook/demo closeout, or deepen the Milestone 5
  Beaverhead-Deerlodge component-inventory build if the user selects that lane.
  The FSH 1909.15 chapter rows remain a scoped workbook/source delta before any graph export can
  claim handbook completeness.

Current stop conditions for the next session:

- Do not treat generated review success as proof of applicability correctness.
- Do not promote compliance-review eval outputs without applicability decision-quality evals.
- Do not let unresolved or `needs_adjudication` decisions become reviewer-ready by default.
- Do not let `compliance-review` override applicability decisions.
- Do not call the raw generated matrix or root-level manual review exports a Forest
  Supervisor-ready EA consistency decision-support document. The generated decision-support report
  is now the gated readiness artifact; root-level `East_Crazies_*` files remain non-canonical manual
  comparison material.
- Do not stage generated `source_library/` artifacts unless repository policy changes explicitly.

## Historical V1 Gate State

The East Crazy Inspiration Divide V1 compliance review has been rerun against the real package at
`source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)`.
The review ID is `v1-cg-ecid-compliance-review`, source set is
`source-set-ba8d0feae79501b8`, rule pack is `nepa-ea-v0` version `0.4.0`, and generated review
artifacts are under `source_library/reviews/v1-cg-ecid-compliance-review/`.

Current cached rerun command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache \
  --docling-timeout-seconds 180
```

Current run result:

- Package extraction wrote `43` manifest rows and `1,265` package chunks.
- Compliance review wrote JSON, Markdown, PDF matrix, and finding graph artifacts.
- Applicability validation covers `377` candidates with `37` applicable and `340` non-applicable
  authorities, no unresolved/adjudication decisions, and `generated_rule_pack_ready=true`.
- Compliance findings: `37` generated-pack findings, all `37` pass.
- All `26` baseline source records were evaluated.
- The profile-driven forest-plan resolver now resolves the package to `scope_status:
  custer_gallatin`; context validation passes and `needs_reviewer_resolution` is `false`.
- Forest-plan component artifacts are now produced from the current source-set inventory:
  `329` component findings, `58` standards, `12` applicable standards, and `12` applied standards.
- Compliance validation passes; the compliance review is reviewer-ready. The stricter
  applicable-standard coverage gate now passes with `all_applicable_standards_applied=true`; the
  prior `AB-STD-RCREA-01` gap is supported by recreation/access package evidence for the proposed
  nonmotorized Sweet Trunk Trail.
- Component-level forest-plan eval now passes all `35` adjudicated cases from
  `config/forest_plan_component_eval_seed.json`: every applicable standard is covered, the case set
  includes representative non-standard component types and hard negatives, case coverage
  requirements pass, and all scored accuracy/citation/section/closure metrics meet strict
  thresholds. Non-standard package evidence now uses strict section-family binding, including
  hydrology, wildlife, botany, scenery, sustainability, recreation/access, land exchange, and
  minerals; regenerated findings have `79` supported components, `0` gaps, no supported package
  evidence with mismatched section binding, and `51` explicit affirmative Plan Consistency Table
  component-row bindings.
- Phase eval passes `10/10` phases after stale component adjudication artifacts are removed;
  `forest_plan_component_eval` passes, and the review is `reviewer_ready=true` at the phase gate.
  Phase eval now rejects stale component-adjudication eval artifacts whose recorded queue count
  differs from the current reviewer-resolution queue.
- V1 real-EA eval now passes the current source/section gate. All `13` required EA section families
  were detected, all `26` baseline authorities matched source records and document roles, citation
  requirements matched, and all Custer Gallatin forest-plan expectations pass, including zero open
  standard reviewer-resolution items.
- `nepa_4336b_programmatic_tiering` remains present and adjudication-pending, but Milestone 4 now
  routes its package evidence to the `alternatives`/`environmental_consequences` context expected by
  the V1 contract. The rule remains source-aligned to `R1EA-005` and document-role aligned to `law`.
- `v1-ea-eval` records separate lanes in `v1_ea_eval_results.json`: `broader_ea`, `forest_plan`,
  and `overall` all pass. Pending conditional adjudication is an explicit accepted V1 risk under
  `conditional_adjudication_policy.mode=accepted_pending_v1`, with exactly `14` pending
  `adjudicate` rows carried in the eval output.

Primary gate artifacts/checks:

- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_context_summary.json` reports
  `scope_status: custer_gallatin`, `reviewer_ready: true`, `validation_passed: true`,
  `needs_reviewer_resolution: false`, `geographic_area_count: 2`, `management_area_count: 1`,
  `overlay_count: 2`, and `supporting_plan_evidence_count: 5`.
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json`
  reports `329` findings: `79` supported, `0` gap, and `250` not applicable.
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json`
  reports `12` applicable standards, `12` applied standards, and
  `all_applicable_standards_applied=true`.
- `source_library/reviews/v1-cg-ecid-compliance-review/compliance_validation.json` passes.
- `v1_ea_eval_results.json` now reports `passed=true`, `broader_ea_passed=true`,
  `forest_plan_passed=true`, empty failure-category counts, `failed_rule_ids=[]`,
  `rule_section_match_rate=1.0`, `conditional_false_positive=0`, and
  `conditional_false_negative=0`.
- V1 EA gate repair milestone 1 locked the failure reproduction without changing applicability,
  trigger, or section-routing behavior. The eval summary now includes
  `failed_rule_expectation_count`, `failed_rule_ids`, `failed_rule_ids_by_category`, and
  `failed_rule_expectations`, naming the three CE false positives
  (`nepa_4336c_ce_adoption_screen`, `usda_nepa_ce_fanec_7cfr_1b3`,
  `usda_nepa_subcomponent_ce_7cfr_1b4`) and the two section mismatches
  (`nepa_statute_chapter_55`, `nepa_4336b_programmatic_tiering`).
- V1 EA gate repair milestone 2 added grouped positive applicability triggers for the three CE/FANEC
  conditional rules. The East Crazies review now keeps those rules `not_applicable` unless package
  evidence shows an adopted CE, CE/FANEC screen, categorical-exclusion path, USDA CE screening, or
  extraordinary-circumstances review. A follow-up gap pass added explicit
  `does_not_apply_if_package_terms` guards so negated same-chunk CE/FANEC language remains
  non-applicable evidence rather than a positive trigger.
- V1 EA gate repair milestone 3 routes `nepa_statute_chapter_55` package evidence to
  purpose-and-need environmental-assessment text. The live V1 eval now reports
  `rule_source_section_expectations_met=true`, `rule_section_match_rate=1.0`, and no
  `nepa_statute_chapter_55` section failure.
- V1 EA gate repair milestone 4 adds rule-declared package section term groups for
  `nepa_4336b_programmatic_tiering` and uses them as a package-evidence ranking/span preference.
  The live V1 eval now reports `nepa_4336b_programmatic_tiering` with actual package sections
  `alternatives` and `environmental_consequences`, actual source record `R1EA-005`, actual source
  document role `law`, and `adjudication_pending=true`. The follow-up gap pass made the new
  package section preference contract explicit in rule-pack validation and output-schema docs.
- V1 EA gate repair milestone 5 makes conditional adjudication explicit. All `18`
  conditional-source expectations now carry classification rationales, the contract accepts exactly
  `14` pending `adjudicate` rows under `conditional_adjudication_policy.mode=accepted_pending_v1`,
  and `v1-ea-eval` emits both a summary and full pending-results queue for those rows.
- V1 EA gate repair milestone 6 promoted the final pre-applicability V1 gate on 2026-05-03. That
  base-pack rerun had `44` findings, `40` pass findings, `4` not-applicable findings, all `26`
  baseline source records evaluated, `191` rule-claim links, and `0` rule-claim gaps. The current
  generated-pack V1 review supersedes it with `37` generated findings, `37` pass findings, `162`
  generated-pack rule-claim links, and `0` rule-claim gaps. `forest-plan-component-eval` passes
  `35/35`, review-bound `phase-eval` passes `21/21`, and `v1-ea-eval` passes broader EA and
  forest-plan lanes. Base-pack compliance-gold eval outputs remain useful through
  `rule_pack_match_mode=generated_base`, but direct base-pack compliance-review reruns are
  diagnostic unless explicitly allowed.
- The forest-plan component adjudication template from the prior run contained `21` pending
  non-standard items: `8` desired conditions, `2` goals, `7` guidelines, `3` objectives, and
  `1` suitability component. Those adjudications classified every item as a system miss, and the
  current resolver fixes now close them with package/plan evidence or correct not-applicable
  determinations. The current reviewer-resolution queue has `0` items, so no component adjudication
  phase is required for the latest phase eval.
- The forest-plan component eval result has been written locally at
  `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_eval_results.json`.
  `phase-eval --review-id v1-cg-ecid-compliance-review` includes it as the passing
  `forest_plan_component_eval` phase.
- A follow-up audit tightened the last two milestone gates: component eval now checks
  review/source-set identity across component findings, applicable-standard coverage, and
  reviewer-resolution queue artifacts; citation correctness requires exact plan/package citation
  sets; phase eval rejects a stale component-eval result schema; and applicable-standard coverage
  fails if any selected standard loses LMP plan-source evidence, even when the standard is not
  applicable.

Historical next implementation target, now superseded:

The V1 EA gate repair plan is complete through Milestone 6. This historical handoff originally
pointed to the revised `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md` as the next target.
Milestones 1 through 9 of that applicability-first plan are now implemented, and the separate
evidence-arbitration gap plan is complete through Milestone 5. The remaining target is Milestone 10
real-package expansion: resolve the ECID preliminary-EA adjudication worklist or add the third real
package fixture. Do not broaden the V1 claim beyond the current Custer Gallatin proving package
without a new evidence-backed plan and gate.

The forest-plan review evaluator now runs component-evaluation V0 by default for packages resolved
to the selected forest-plan profile. Mandatory component evaluation is committed at `8f607e4`, and
the NFMA standard-coverage gate is committed at `21d30b6`.

Current session update:

- Forest-plan component adjudication tooling has been added. The template command exports current
  reviewer-resolution queue items to a stable adjudication contract plus a Markdown reviewer
  worklist; the eval command checks identity, queue coverage, completed adjudication metadata,
  resolved dispositions, and expected current status matches. Phase eval now surfaces the
  adjudication eval as a readiness phase when that artifact is present.
- The adjudication disposition taxonomy is explicit data: `true_ea_omission`, `retrieval_miss`,
  `package_section_chunking_miss`, `component_inventory_overreach`,
  `applicability_false_positive`, and `evidence_linking_miss`.
- The adjudication eval separates dispositions into `real_ea_omission` versus `system_miss`
  outcome metrics. The prior East Crazies forest-plan adjudication classified all `21` resolved
  non-standard component items as system misses and none as real EA omissions; the current queue is
  closed through resolver fixes.
- Profile-driven forest-plan scope resolution now distinguishes operative selected-profile evidence
  from incidental references to other forests. Background/reference mentions of another configured
  forest no longer force `ambiguous`, while operative evidence that the project is on another forest
  still blocks Custer Gallatin resolution.
- Negative package-location rows such as `not part of the project area` are filtered before
  geographic or management area entries are resolved.
- The real East Crazy Inspiration Divide package now resolves to Custer Gallatin scope and produces
  forest-plan component artifacts from the source-set inventory; the V1 eval contract now expects
  the generated `R1PLAN-custer-gallatin-nf-02-...` component IDs instead of the old seed fixture IDs.
- Forest-plan component evaluation V0 has been added as a required `forest-plan-resolve` stage for
  packages resolved to the selected forest-plan profile; `--forest-plan-component-inventory-path`
  only overrides the inventory path.
- Component outputs are `forest_plan_component_findings.json`,
  `forest_plan_component_findings.md`, `forest_plan_reviewer_resolution_queue.json`,
  `forest_plan_component_inventory_coverage.json`, and
  `forest_plan_applicable_standard_coverage.json`; forest-plan rows are linked from the
  review-level compliance matrix JSON, Markdown, and PDF.
- `config/forest_plan_component_inventory_seed.json` contains the first narrow Custer Gallatin seed
  inventory for East Crazies-relevant Crazy Mountains Backcountry Area components.
- Component validation now fails closed on source-set drift, requires supported/partial findings to
  carry both package and plan-source evidence, and turns missing package evidence into
  reviewer-resolution queue items.
- NFMA standard coverage V0 writes `forest_plan_component_inventory_coverage.json` and
  `forest_plan_applicable_standard_coverage.json`.
- Component findings now carry a structured `compliance_status`; applicable standards require
  plan-source evidence, EA package evidence, and a resolved compliance status before component
  validation can pass.
- `forest-plan-components-build` now writes source-set inventory artifacts plus
  `component_inventory_build_coverage.json`, proving selected forest-plan chunks, detected component
  labels, detected standard labels, missing detected standards, duplicate standards, and generated
  record validation before a built inventory can pass. Current build coverage also records `2`
  suppressed component-like labels with nonnumeric number tokens, such as cross-reference/table
  headings, as non-blocking inventory-quality issues instead of allowing rough IDs into the
  inventory.
- Source-set generated component inventories under
  `source_library/derived/<source_set_id>/forest_plan_components/` must have passing build coverage
  before `forest_plan_component_inventory_coverage.json` can pass during NFMA component evaluation.
- Sequence 3 forest-plan improvement work has started with a durable East Crazies fixture under
  `tests/fixtures/forest_plan_evaluator/east_crazies_profile_driven.txt`.
- The fixture proves Custer Gallatin scope, Bridger/Bangtail/Crazy Mountains Geographic Area, Crazy
  Mountains Backcountry Area, required Custer Gallatin source-record readiness, FEIS/BA/BO
  supporting routes from explicit package evidence, and reviewer-ready gating.
- Custer Gallatin ROD trigger terms were tightened so generic project decision labels such as
  `selected alternative`, `decision basis`, `objection resolution`, or `plan approval` do not route
  to the forest-plan ROD unless the package explicitly says `Record of Decision` or `ROD`.
- FEIS trigger terms were tightened so generic `plan consistency` labels do not activate FEIS
  routing unless an explicit FEIS, tiering, or incorporation cue is present.
- `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md` was rewritten around current RAG/legal
  RAG research: structured authority components, precise snippet retrieval, graph relationships,
  W3C PROV-style provenance, RAG-triad-style evaluation, and fail-closed audit gates.

Recent sequence commits:

- `aadbc53` - Add forest plan review harness contract
- `f11191c` - Sequence 1: add forest plan profile loader
- `c0da944` - Sequence 1 hardening: tighten profile validation
- `270bfa7` - Sequence 2: drive forest plan resolver from profiles
- `3ca34f7` - Sequence 2 hardening: close profile resolution gaps
- `8f607e4` - Add mandatory forest plan component review
- `21d30b6` - Add NFMA standard coverage gate
- `ab7f034` - Fix forest plan component inventory CLI override
- `ca29dfa` - Add forest plan component inventory builder

Implemented behavior:

- `config/forest_plan_profiles.json` contains the first forest-plan profile for Custer Gallatin.
- `forest-plan-resolve` reads forest names, ambiguous terms, required source records, area terms,
  overlays, and supporting evidence routes from the selected profile.
- `forest-plan-resolve` writes component findings, a Markdown rendering, and a reviewer-resolution
  queue from a data inventory for packages resolved to the selected forest-plan profile.
- `forest-plan-resolve` also writes selected-inventory coverage and applicable-standard coverage;
  reviewer-ready status fails when an applicable standard lacks plan evidence, package evidence, or a
  resolved compliance status.
- `forest-plan-components-build` can produce rebuildable source-set component inventories and build
  coverage from extracted forest-plan chunks.
- The current Custer Gallatin LMP inventory for `source-set-ba8d0feae79501b8` has been generated
  from extracted chunks with `329` components, `58` standards, and passing build coverage. The seed
  inventory is now a fallback/test fixture.
- Built source-set inventories fail inventory coverage when their adjacent build coverage is missing
  or failed, which prevents them from being silently used as NFMA compliance evidence.
- Default Custer Gallatin V0 output compatibility is preserved: `scope_status` still uses
  `custer_gallatin`, `not_custer_gallatin`, or `ambiguous`.
- `--forest-unit-id` and `--forest-plan-profiles-path` allow the resolver to run against another
  configured profile path.
- Other configured profiles are treated as known out-of-scope forests when Custer Gallatin is the
  selected profile.
- Default profile loading works from outside the repository working directory.

Latest verification:

Current profile-driven resolver fix verification on 2026-05-03:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --review-id v1-cg-ecid-compliance-review --reuse-package-cache
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" --output-dir source_library --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --source-set-id source-set-ba8d0feae79501b8 --review-id v1-cg-ecid-compliance-review --reuse-package-cache --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/forest_plan_component_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/v1_ecid_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-template --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --adjudication-file source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_adjudication_template.json
UV_CACHE_DIR=/private/tmp/usfs_uv_cache PYTHONPATH=src uv run --extra dev pytest
UV_CACHE_DIR=/private/tmp/usfs_uv_cache PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/v1_ecid_real_ea_eval.json /private/tmp/v1_ecid_real_ea_eval.validated.json
git diff --check
```

Results from the latest pre-applicability live rerun: compliance review passed with `40` pass
findings and `4` not applicable findings; the current generated-pack review supersedes that with
`33` pass findings and `0` compliance not-applicable rows because non-applicable authorities now
live in `non_applicable_authorities.json`. Forest-plan context validation passes with `2`
geographic areas, `1` management area, `2` overlays, and `5` supporting plan-evidence routes.
Forest-plan component validation now passes: `329` components, `58` standards, `12` applicable
standards, `12` applied standards, `0` reviewer-resolution items, and zero unresolved applicable
standards. The prior
`AB-STD-RCREA-01` standard gap and the prior `21` non-standard queue items now have evidence-backed
support or correct not-applicable determinations. Component-level forest-plan eval passes all `35`
adjudicated cases with all-applicable-standard coverage. `phase-eval` passes `10/10` phases and
reports `reviewer_ready=true`;
`v1-ea-eval` now passes with forest-plan expectation match rate `1.0`,
section detection/source-record/document-role rates `1.0`, zero open standard reviewer-resolution
items, empty failure-category counts, and `failed_rule_ids=[]`.

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_compliance_review.py tests/test_forest_plan_resolver.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --source-record-id R1PLAN-custer-gallatin-nf-02 --forest-unit-id custer-gallatin-nf --plan-version 2022
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --gold-file config/compliance_gold_eval_v0.json
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/forest_plan_component_eval_seed.json
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
python -m json.tool config/forest_plan_profiles.json /tmp/forest_plan_profiles.validated.json
python -m json.tool config/forest_plan_component_inventory_seed.json /tmp/forest_plan_component_inventory_seed.validated.json
python -m json.tool config/forest_plan_component_eval_seed.json /tmp/forest_plan_component_eval_seed.validated.json
git diff --check
```

Earlier forest-plan sequence verification: full test suite passed with `220 passed, 5 subtests
passed`; focused forest-plan component eval tests passed with `5 passed`; focused component-eval
phase test passed; lint, compile, JSON validation, and whitespace checks passed. The current
EA-gate milestone reran the compliance review and all promotion gates; `v1-ea-eval` now passes
with `broader_ea_passed=true`, `forest_plan_passed=true`, empty failure-category counts,
`conditional_false_positive=0`, `conditional_false_negative=0`, and forest-plan expectation match
rate `1.0`.

## Next Sequence

The next selected sequence depends on the lane being continued. For a focused final East Crazy
compliance-review QA/certification replay, use
`docs/EAST_CRAZIES_FINAL_QA_CERTIFICATION_MILESTONE_PLAN.md` and begin with Sequence 0 baseline
replay and drift check. For strict real-package expansion, continue with the South Plateau
forest-plan context plan in `docs/SOUTH_PLATEAU_FOREST_PLAN_CONTEXT_MILESTONE_PLAN.md`.

Current V1 promotion remains green, ECID remains a ready expansion slot, and South Plateau is
intentionally blocked from strict expansion by `forest_plan_reviewer_not_ready` until its declared
Custer Gallatin forest-plan context is reviewer-ready or the blocker is narrowed by verified
resolver evidence. Future package expansion beyond that should start as a new real-package slot
with its own package fixture, applicability artifacts, generated review artifacts, promotion-suite
review-case checks, and docs/handoff closeout.

The V1 EA gate repair plan is closed. The current East Crazy Inspiration Divide review artifacts
were regenerated and verified, and the V1 EA gate is promoted after the broader EA lane,
forest-plan lane, phase eval, compliance-review eval, and gold eval all passed.

Candidate post-V1 goals:

- Broaden from the Custer Gallatin proving package to additional real Region 1 EA packages.
- Add embeddings/reranking behind the existing deterministic source, citation, and eval gates.
- Add model-assisted synthesis as a report layer without changing the deterministic readiness
  contract.
- Expand the adjudicated real-package eval set beyond the current Custer Gallatin V1 package and
  10-case compliance-gold fixture.

Non-goals:

- Do not broaden the claim to all Region 1 forests.
- Do not stage ignored generated `source_library/` outputs unless repository policy changes.
- Do not weaken source-record, document-role, citation, section, forest-plan, phase-eval, or
  validation gates.

Relevant files:

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/V1_DEMO_DOCUMENT_REVIEW_MILESTONE_PLAN.md`
- `README.md`
- focused source/test/config changes from the prior gate-repair milestones

Current promoted eval signal:

- `v1-ea-eval` reports `passed=true`, `broader_ea_passed=true`, and `forest_plan_passed=true`.
- `phase-eval --review-id v1-cg-ecid-compliance-review` reports all phases passing.
- Compliance review eval and gold eval remain promotion-ready.

Promotion verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/v1_ecid_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --gold-file config/compliance_gold_eval_v0.json
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Future post-V1 sequences should stage only their verified slice and commit atomically.

Stop conditions for the next plan:

- The proposed post-V1 scope would weaken source-record, document-role, citation, section,
  forest-plan, phase-eval, or validation gates.
- The proposed work would broaden the reviewer-ready claim beyond the current evidence-backed
  Custer Gallatin package without new eval coverage.
- Generated `source_library/` artifacts would need to become tracked without an explicit repository
  policy change.

Expert alignment notes retained from the earlier forest-plan sequence:

- Scott Vandegrift: readiness and reuse should be explicit; avoid unnecessary full-corpus rebuilds.
- Chuck Nicholson: the fixture should look like practitioner QA/QC, with transparent criteria and
  actionable gaps.
- Liz Esposito: every supported result must keep source-record IDs and evidence basis visible; do
  not convert the fixture into a legal conclusion.

Milestone 5 alignment closeout:

- Pending conditional rows are explicit accepted V1 risk, not resolved legal conclusions.
- Malformed conditional-adjudication policy counts or rule-ID lists fail contract validation.

Milestone 6 alignment closeout:

- The final V1 gate promotion passed through phase eval, V1 eval, compliance-review eval, gold eval,
  full tests, lint, compile, JSON validation, and docs promotion.
- The next milestone is outside the V1 EA gate repair plan.

## Gold Coverage Expansion Plan Refresh

The gold-coverage plan at `docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md` is now refreshed
against the live 2026-05-13 gold outputs rather than only the earlier abstract gap description.

- refreshed problem statement:
  the live applicability-gold result still records `case_count=5`,
  `adjudicated_covered_family_count=1`, `negative_covered_family_count=0`, and
  `authority_family_template_coverage.passed=false` while top-level `promotion_ready=true`; the
  live compliance-gold result records `passed=true` but `promotion_ready=false`; and the only
  shipped real-package contract still remains `config/v1_ecid_real_ea_eval.json`
- tightened routing:
  the refreshed plan now explicitly treats the remaining weakness as adjudicated gold breadth,
  real-package contract breadth, and promotion wiring above the already-broad generic
  `applicability_eval` lane, which already covers all current `19` high-priority authority
  families in positive and negative direct eval
- new contract requirement:
  the milestone now requires `config/gold_coverage_v1.json` to own all current `19`
  `high_priority_family_ids`, map them into required gold coverage groups, and fail when top-level
  gold summaries mask red nested family/group coverage
- required missing artifacts called out up front:
  `config/gold_coverage_v1.json`,
  `config/v1_west_reservoir_real_ea_eval.json`,
  `config/v1_south_plateau_real_ea_eval.json`,
  and tracked package-authority surfaces for East Crazies current promotion and South Plateau
- next routing boundary:
  execute Sequence 0 from the refreshed gold-coverage plan when implementation begins; do not
  reopen `config/applicability_eval_seed.json` or the generic authority-template search lane unless
  the gold milestone first proves the current `19`-family direct-eval surface is wrong

Verification in this planning refresh:

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/GOLD_COVERAGE_EXPANSION_MILESTONE_PLAN.md`: passed
- `git diff --check`: passed

## Real-Package Review Coverage Plan Added

The repo now has a fresh stacked follow-on plan at
`docs/REAL_PACKAGE_REVIEW_COVERAGE_MILESTONE_PLAN.md`. This plan starts only after the refreshed
gold-coverage milestone closes green and is committed.

- routing boundary:
  Milestone 0 of the new plan must re-evaluate the live repo state before implementation begins and
  adopt any equivalent real-package artifacts already created by the gold-coverage milestone instead
  of duplicating them under new names
- governed gap:
  the lane is still East-Crazies-centric because `config/v1_ecid_real_ea_eval.json` remains the
  only shipped per-review V1 contract, `v1_ea_eval.py` still defaults to that ECID contract, and
  the evaluation-coverage register still has no explicit real-package review coverage row
- current live nuance preserved in the new plan:
  West Reservoir is currently reviewer-ready, while South Plateau is still a typed blocked package
  lane; the plan therefore requires explicit ready-versus-blocked slot semantics rather than a fake
  all-green multi-package contract
- expected implementation shape:
  tracked review-slot manifest plus package-authority ownership, per-review West Reservoir and South
  Plateau contracts, removal of implicit ECID-only defaulting, and one aggregate real-package
  coverage gate

Verification in this planning refresh:

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/REAL_PACKAGE_REVIEW_COVERAGE_MILESTONE_PLAN.md`: passed
- `git diff --check`: passed

## Phase-Eval Direct-Eval Gating Plan Refresh

`docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` is now refreshed against the live
2026-05-13 repo state and the new predecessor stack.

- stacked routing:
  the plan now starts only after `docs/REAL_PACKAGE_REVIEW_COVERAGE_MILESTONE_PLAN.md` closes
  green and is committed, and Sequence 0 must adopt any equivalent review-slot or aggregate
  real-package coverage artifacts that predecessor milestone lands
- refreshed current evidence:
  `config/phase_eval_direct_eval_v1.json` is still absent, `evidence_graph.py` still reduces
  source-set readiness to `all(phase["passed"])` and `all(phase["reviewer_ready"])`, `_phase(...)`
  still only emits `phase_validation_failed` and `phase_not_reviewer_ready`, the evaluation
  coverage register still has no explicit `phase_eval` row, and `promotion_suite_v1.json` still
  keys core phase readiness off phase counts rather than direct-eval counters
- review-scope routing tightened:
  the refreshed plan now requires review-scoped `phase-eval` to reuse the predecessor
  real-package coverage owner for declared contract-backed reviews instead of inventing a second
  review roster inside `phase-eval`
- updated closeout gate:
  the full verification stack now includes the predecessor real-package coverage gate before
  review-scoped `phase-eval` and promotion closeout

Verification in this planning refresh:

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`: passed
- `git diff --check`: passed

## Phase-Eval Direct-Eval Gating Gap-Close Refresh

The phase-eval direct-eval milestone now has an explicit architecture-safe remainder route. The
direct-eval seam itself is implemented locally, but closeout is still blocked on live prerequisite
owners.

- implemented seam in worktree:
  `config/phase_eval_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  focused `src/usfs_r1_ea_sources/evidence_graph.py`,
  updated `config/promotion_suite_v1.json`,
  `docs/architecture_contract.toml`,
  and focused tests under
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_evidence_graph.py`,
  `tests/test_compliance_review.py`,
  `tests/test_claim_extraction.py`,
  and `tests/test_promotion_suite.py`
- code-level verification now passes:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_compliance_review.py tests/test_applicability_eval.py tests/test_v1_ea_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py` `147/147`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src python -m compileall src`,
  and `git diff --check`
- live blocker 1:
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-ba8d0feae79501b8`
  now fails `validation_passed` and `reviewer_ready` because the refreshed retrieval summary
  carries the separate verified-extraction prerequisite
  `flathead-forest-plan-direct-extraction` with
  `verified_extraction_admitted_source_count=0` and
  `verified_extraction_required_source_count=1`
- live blocker 2:
  `PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8`
  fails `2/12` cases (`scoping-public-comment`, `decision-notice-mitigation`), so
  source-set `phase-eval` now fails closed with `threshold_failed_phase_count=1` and
  `retrieval` marked `direct_eval_failed`
- live blocker 3:
  `config/replay_contexts/v1-cg-ecid-compliance-review.json` currently sets
  `catalog_dir=source_library/derived/source-set-ba8d0feae79501b8`, and that path is not a real
  catalog surface. Review-scoped `phase-eval --review-id v1-cg-ecid-compliance-review` therefore
  mixes the real retrieval red with a stale replay-context `catalog_capture` red
- promotion consequence:
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
  now reports `current_promotion_ready=false`; the failing current-promotion suite check is
  `phase_eval_threshold_failed_phase_count`
- architecture guard preserved:
  source-set `rule_claim_binding` direct eval remains owned by the canonical base lane under
  `source_library/derived/<source_set_id>/rule_claim_links/nepa-ea-v0/0.4.0/`.
  Do not repoint it at review-generated rule-pack eval outputs just because a review-scoped phase
  selected a different rule-claim summary artifact

Next step if this lane is resumed:

1. Execute the new Sequence 0A and Sequence 0B in
   `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` before further phase-eval edits:
   repair the tracked ECID replay-context catalog ownership, then determine whether ba8d retrieval
   red is a prerequisite-owner repair or a true retrieval direct-eval regression.

## Cross-Forest Profile Eval Coverage Plan Added

The repo now has a fresh stacked follow-on plan at
`docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`. This plan starts only after
`docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` closes green and is committed.

- routing boundary:
  Milestone 0 of the new plan must re-evaluate the live Region 1 roster, adopt any equivalent
  predecessor phase-eval/direct-eval artifacts under their implemented names, and refresh later
  commands before implementation begins
- governed gap:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` currently records only `1` `covered`
  profile, `2` `fixture_contract_defined` profiles, and `7` validated-but-`not_started` profiles,
  so resolver and selected-profile compliance improvements outside the current proving slices are
  still under-protected
- plan shape:
  the new lane is explicitly evaluation-contract scoped, not a revival of the retired
  multi-forest reviewer-ready expansion plan; it requires a governed cross-forest profile eval
  producer, eliminates `not_started`, raises Beaverhead and Flathead above their current `1`/`1`
  placeholder contracts, and wires the resulting producer into the direct-eval-aware
  phase-eval/promotion route
- readiness semantics preserved:
  the plan explicitly keeps eval coverage distinct from reviewer-ready and live-package proof, so
  closing this lane does not overclaim that all Region 1 profiles are operationally proven

Verification in this planning refresh:

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md`: passed
- `git diff --check`: passed

## Forest-Plan Component Eval Coverage Plan Added

The repo now has a fresh stacked follow-on plan at
`docs/FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MILESTONE_PLAN.md`. This plan starts only after
`docs/R1_CROSS_FOREST_PROFILE_EVAL_COVERAGE_MILESTONE_PLAN.md` closes green and is committed.

- routing boundary:
  Milestone 0 of the new plan must re-evaluate the live component-coverage roster, adopt any
  equivalent predecessor profile-eval or phase-eval direct-eval artifacts under their implemented
  names, and decide explicitly whether South Plateau belongs in this coverage boundary or remains
  routed out
- governed gap:
  the current component-eval surface is still local to ECID because the default contract remains
  `config/forest_plan_component_eval_seed.json`, `config/forest_plan_component_evals/` currently
  contains only the ECID replay contract, there is no
  `config/forest_plan_component_evals/west-reservoir-67436.json`, and there is still no standalone
  component-retrieval precision/recall eval producer in live code or config
- current live nuance preserved in the plan:
  `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_eval_results.json`
  exists and passes with `35` cases, while
  `source_library/reviews/west-reservoir-67436/forest_plan_component_eval_results.json` is
  currently missing despite West Reservoir being one of the main non-Custer proving reviews
- expected implementation shape:
  the new lane requires a standalone component-retrieval eval producer, a tracked multi-review
  component-eval coverage manifest, a West Reservoir review contract, removal of hidden
  ECID-only defaulting for tracked review IDs, and wiring of the new producers into the
  direct-eval-aware phase-eval/promotion route

Verification in this planning refresh:

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MILESTONE_PLAN.md`: passed
- `git diff --check`: passed
