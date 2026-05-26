# Reviewer-Facing Source-Set Alignment Blocker Milestone Plan

Date: 2026-05-25
Status: Active packet (`Milestone 0` gate-and-routing opener resolved locally; `Milestone 1` reviewer-facing authority-surface alignment is next)
Owner context: standalone blocker follow-on opened after
`docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` proved that the
scoped replay-precondition lane on `source-set-f70ea11e04ae3d53` is green but
reviewer-facing replay on `source-set-4fb59e9eb43045cb` is still upstream
blocked. This packet owns reviewer-facing source-set alignment only. It does
not pretend packet-local review artifacts are repaired, and it does not reopen
full-canonical source capture, downloader, or slot-driven promotion-suite
architecture.

## Purpose

Repair the reviewer-facing source-set authority-surface mismatch that now
blocks truthful replay on the governed real-package review lane.

The replay-repair packet exhausted the scoped current-source and
derived-artifact prerequisites on `source-set-f70ea11e04ae3d53`, but live
reviewer-facing runs still bind to historical `source-set-4fb59e9eb43045cb`.
That older reviewer-facing source set no longer satisfies the authority-source
requirements needed by ECID and South Plateau. Until reviewer-facing replay
contexts, eval contracts, and review-local authority surfaces are aligned to
one governed source-set truth, packet-local reruns cannot honestly restore the
reviewer-ready slots.

## Current Evidence

- `real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`
  reports `passed=false`, `reviewer_ready_slot_count=0`, and
  `typed_blocked_slot_count=1`; both ECID and South Plateau are mismatched
  while West Reservoir remains truthfully `typed_blocked`.
- `v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`
  reports `contract_status="mismatch"` with missing review-local compliance
  artifacts plus broader `baseline_source_record_missing`,
  `citation_requirement_miss`, `conditional_false_negative`,
  `review_artifact_missing`, `rule_section_mismatch`, and
  `forest_plan_matrix_miss` failures.
- `phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`
  fails on stale review-local artifacts and source-set direct-eval debt. The
  false extraction-owner dependency is now repaired locally by moving
  extraction direct-eval ownership to `extraction-fidelity-eval`, so the
  remaining red is truthful replay debt rather than a stale phase-eval
  contract.
- `applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`
  and the matching South Plateau run both report
  `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=1d0385d00ac80eb1975b9ccfce137e13c37a0751800b98c0a9fff7a3d1790d6b`,
  `validation_passed=false`,
  `candidates_have_source_evidence_available failure_count=10`, and
  `authority_family_template_candidates_cover_config missing_source_record_count=11`.
- The scoped gate on `source-set-f70ea11e04ae3d53` is no longer the blocker:
  `reuse-inventory`, `extract-build`, `extraction-accuracy-audit`,
  `retrieval-build`, `claim-extract`, `rule-claim-link`, and
  `applicability-authority-universe` now pass there with
  `authority_universe_sha256=33355dce05cb0141840bf5ad6463570173294e6e1a368d0e24f8910961a04554`.
- Attempted ECID `compliance-review` reruns on reviewer-facing
  `source-set-4fb59e9eb43045cb` fail before substantive replay because the
  generated applicability rule pack is not truthful on that source set.

## Goal

Restore one governed reviewer-facing source-set truth so replay-preflight
commands stop failing on mixed or stale authority surfaces.

Completion means all of the following are true:

- ECID and South Plateau reviewer-facing applicability reruns pass on the same
  governed source-set identity with no reviewer-facing source-evidence or
  missing-source-record template failures.
- reviewer-facing replay contexts, coverage contracts, and source-set-aware
  validators describe that same governed source-set truth.
- `v1-ea-eval`, `phase-eval`, and real-package coverage reruns no longer fail
  because the reviewer-facing source set is missing prerequisite authority
  surfaces; if they remain red, the remaining failures are packet-local review
  artifacts and are routed back to the replay-repair packet truthfully.

## Non-Goals

- Do not reopen downloader, catalog-build, or workbook current-source
  admission work unless the reviewer-facing alignment proof shows that a
  fresh governed reviewer-facing catalog is strictly required.
- Do not weaken `v1-ea-eval`, `phase-eval`,
  `real-package-review-coverage-eval`, or `promotion-suite` to hide stale
  reviewer-facing source-set debt.
- Do not claim ECID or South Plateau reviewer-ready status in this packet
  unless the packet-local artifact families are actually refreshed.
- Do not alter West Reservoir's `typed_blocked` quarantine.
- Do not stage ignored `source_library/` outputs unless repository policy
  changes or the user explicitly expands scope.

## Scope

- reviewer-facing source-set owner mapping for ECID and South Plateau
- replay-context, eval-contract, and source-set-aware validator alignment
- `phase-eval` direct-eval ownership alignment needed to make the blocker
  truthful
- docs and handoff rerouting so future sessions land on the blocker instead of
  stale packet-local replay
- focused replay-preflight reruns that prove when control can return to the
  replay-repair packet

## Out Of Scope

- packet-local review artifact repair for ECID or South Plateau
- full-canonical source-truth, queue, or downloader lane changes
- roster redesign for `config/v1_real_package_review_coverage_v1.json`
- promotion-suite selector or quorum semantics

## Owner Surfaces

- reviewer-facing contracts:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/v1_ecid_real_ea_eval.json`,
  `config/v1_south_plateau_real_ea_eval.json`
- replay contexts:
  `config/replay_contexts/v1-cg-ecid-compliance-review.json`,
  `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`
- phase-eval direct-eval ownership:
  `config/phase_eval_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_support.py`
- reviewer-facing command owners:
  `src/usfs_r1_ea_sources/v1_ea_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval.py`,
  `src/usfs_r1_ea_sources/real_package_review_coverage_eval.py`,
  `src/usfs_r1_ea_sources/cli_applicability.py`
- focused tests:
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_phase_eval.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_v1_ea_eval_contracts.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_architecture_contract.py`
- durable docs:
  `README.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep reviewer-facing source-set selection declarative. Prefer replay-context
  or eval-contract surfaces over hidden runtime branches or ad hoc artifact
  patching.
- Keep extraction direct-eval ownership in the dedicated phase-eval
  direct-eval support/runtime surfaces. Do not reintroduce extraction ownership
  through generic upstream-eval assumptions.
- If a new validator or helper is needed, place it next to the existing
  reviewer-facing command surface it protects and cover it with a focused test.
- Do not mix this blocker packet with packet-local compliance, decision
  support, final-QA, or review-packet rewrites unless a rerun proves they are
  the next truthful owner after alignment is repaired.

## Weak-Point Prevention Contract

### Weak Point 1

- Weak point forecast:
  reviewer-facing configs may keep mixing `source-set-4fb59e9eb43045cb` and
  `source-set-f70ea11e04ae3d53`, creating false-green or permanently stale
  replays.
- Owner surface:
  replay contexts, real-package coverage contracts, and source-set-aware
  validators.
- Prevention gate:
  rerun ECID and South Plateau `applicability-authority-universe` on the
  governed reviewer-facing source set plus focused contract tests.
- Fail threshold:
  either reviewer-facing run still reports
  `candidates_have_source_evidence_available failure_count>0` or
  `authority_family_template_candidates_cover_config missing_source_record_count>0`.
- Controlled violation:
  keep one focused test that fails when a replay context or reviewer-facing
  contract points at a different source-set identity than the governed replay
  preflight owner.
- Future-Codex misuse scenario:
  a future session may patch only one review's config or point coverage
  manifests at a new source set without updating the replay contexts. The gate
  prevents that split-brain route from landing.

### Weak Point 2

- Weak point forecast:
  `phase-eval` may regress back to treating extraction direct-eval as a
  generic upstream-eval artifact, masking the real blocker with a stale owner
  assumption.
- Owner surface:
  `config/phase_eval_direct_eval_v1.json` and the
  `phase_eval_direct_eval*` support/runtime modules.
- Prevention gate:
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_phase_eval.py`, and a live `phase-eval` rerun for ECID.
- Fail threshold:
  extraction direct-eval is sourced from any producer other than
  `extraction_fidelity_evaluation`, or a reviewer-facing `phase-eval` failure
  reintroduces a false extraction-owner miss.
- Controlled violation:
  keep the negative-path contract test that fails when the extraction fidelity
  results path is missing or schema-invalid.
- Future-Codex misuse scenario:
  a future session may copy an older upstream-eval contract row and silently
  undo the direct-eval owner split. The focused contract tests must fail first.

### Weak Point 3

- Weak point forecast:
  docs and handoff may continue routing agents into the replay-repair packet
  even though that packet cannot advance truthfully.
- Owner surface:
  `README.md`, `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`, `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  and `docs/SESSION_HANDOFF.md`.
- Prevention gate:
  `git diff --check`, the milestone-plan linter, and a targeted grep over the
  routed docs for stale "next truthful slice" references before commit.
- Fail threshold:
  any top-of-doc routing surface still points new work at packet-local replay
  on `source-set-4fb59e9eb43045cb` before the alignment blocker is cleared.
- Controlled violation:
  keep the new blocker packet named in every top-level route surface; if one
  is omitted, the grep review fails the milestone.
- Future-Codex misuse scenario:
  a future session may read only the README or handoff and start rerunning the
  wrong packet. The doc route must be fail-closed and consistent.

## Milestone Sequence

### Milestone 0 - Gate And Routing Opener

Outcome label: resolved

Purpose: prove the stale replay route is wrong, align the extraction direct-eval
owner so the blocker is truthful, and open this standalone blocker packet.

Implementation:

1. Run the live ECID, South Plateau, applicability, and aggregate coverage
   commands needed to prove packet-local replay on `source-set-4fb59e9eb43045cb`
   is upstream-blocked.
2. Move extraction direct-eval ownership in `phase-eval` from generic
   upstream-eval assumptions to `extraction-fidelity-eval` and add focused
   regressions.
3. Open this blocker packet and reroute all top-level docs and handoff surfaces
   so future sessions land here first.

Acceptance criteria:

- `tests/test_phase_eval_direct_eval_contracts.py` and `tests/test_phase_eval.py`
  pass with extraction direct-eval owned by
  `extraction_fidelity_evaluation`.
- top-level route docs all identify this packet as the next truthful slice.
- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` truthfully records
  that replay repair stopped at reviewer-facing source-set alignment.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --source-set-id source-set-4fb59e9eb43045cb

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment \
  --source-set-id source-set-4fb59e9eb43045cb

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_phase_eval_direct_eval_contracts.py \
  tests/test_phase_eval.py \
  tests/test_architecture_contract.py -q

python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py \
  --strict docs/REVIEWER_FACING_SOURCE_SET_ALIGNMENT_BLOCKER_MILESTONE_PLAN.md

git diff --check
```

### Milestone 1 - Reviewer-Facing Authority-Surface Alignment

Outcome label: resolved

Purpose: align reviewer-facing replay to one governed source-set truth so
upstream applicability and generated-rule-pack prerequisites are no longer red.

Implementation:

1. Freeze the governed reviewer-facing source-set strategy:
   either rebind reviewer-facing replay to `source-set-f70ea11e04ae3d53` or
   create the minimal refreshed reviewer-facing source set that preserves the
   same governed authority surfaces. Do not proceed with mixed source-set
   identities.
2. Update the replay contexts, reviewer-facing eval contracts, and any
   source-set-aware validators that still point at the wrong source-set truth.
3. Rerun `applicability-authority-universe` for both ECID and South Plateau on
   the governed reviewer-facing source set until the source-evidence and
   missing-source-record template failures are zero.
4. If a generated applicability rule pack is expected downstream, regenerate
   and verify only the minimal reviewer-facing artifacts needed to prove the
   source-set alignment is truthful.

Acceptance criteria:

- both reviewer-facing applicability reruns pass on the same governed
  source-set identity.
- reviewer-facing contract/config surfaces no longer disagree about which
  source set owns replay-preflight truth.
- if `v1-ea-eval` or `phase-eval` remain red after the alignment reruns, their
  remaining failures are packet-local review artifacts rather than source-set
  authority-surface debt.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --source-set-id <governed-reviewer-facing-source-set-id>

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment \
  --source-set-id <governed-reviewer-facing-source-set-id>

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_v1_ea_eval.py \
  tests/test_v1_ea_eval_contracts.py \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_phase_eval.py \
  tests/test_architecture_contract.py -q

PYTHONPATH=src uv run --extra dev ruff check src tests
```

### Milestone 2 - Replay-Preflight Confirmation And Reroute Closeout

Outcome label: resolved

Purpose: prove the alignment blocker is gone and hand control back to the
packet-local replay-repair lane truthfully.

Implementation:

1. Rerun ECID and South Plateau `v1-ea-eval` plus ECID `phase-eval` on the
   aligned reviewer-facing source set.
2. Confirm that any remaining red in those commands is packet-local review
   artifact debt rather than reviewer-facing source-set mismatch.
3. Update durable docs and the handoff with the aligned source-set truth, the
   exact remaining packet-local failures, and the return route back to
   `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` if appropriate.

Acceptance criteria:

- reviewer-facing preflight commands no longer fail because of missing
  authority surfaces on the chosen source set.
- the next truthful slice is either packet-local replay repair on the aligned
  reviewer-facing source set or a newly opened narrower follow-on backed by the
  verified outputs.
- this blocker packet closes with docs, handoff, verification, and one atomic
  commit.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources v1-ea-eval \
  --output-dir source_library \
  --review-id region1-expansion-south-plateau-landscape-treatment

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources real-package-review-coverage-eval \
  --output-dir source_library \
  --manifest config/v1_real_package_review_coverage_v1.json

PYTHONPATH=src uv run --extra dev pytest \
  tests/test_v1_ea_eval.py \
  tests/test_v1_ea_eval_contracts.py \
  tests/test_real_package_review_coverage_eval.py \
  tests/test_phase_eval.py \
  tests/test_architecture_contract.py -q

PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

## Required Implementation Artifacts

- any replay-context, eval-contract, or validator updates needed to bind
  reviewer-facing replay to one governed source-set truth
- focused phase-eval direct-eval owner alignment changes and regression tests
- durable route docs and handoff updates that point to the active blocker
  packet and later route back to replay repair truthfully

## Required Documentation And Handoff Updates

- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- `docs/SESSION_HANDOFF.md`
- this blocker plan file

## Required Verification Gates

- reviewer-facing `applicability-authority-universe` for both ECID and South
  Plateau
- ECID `v1-ea-eval` and `phase-eval`, plus South Plateau `v1-ea-eval`
- focused pytest coverage for phase-eval direct-eval contracts and
  reviewer-facing eval contracts
- `ruff check src tests`
- `git diff --check`
- milestone-plan linter with `--strict` whenever this plan file changes

## Acceptance Criteria

- No routed top-level doc still claims packet-local replay on
  `source-set-4fb59e9eb43045cb` is the next truthful slice before reviewer-facing
  source-set alignment is repaired.
- Reviewer-facing replay-preflight commands use one governed source-set truth
  and pass the authority-surface gates required to begin packet-local replay.
- Extraction direct-eval ownership remains explicitly bound to
  `extraction-fidelity-eval` in config, runtime, and tests.
- Any remaining review failures after alignment are explicitly named as
  packet-local artifact debt, not hidden behind source-set ambiguity.

## Stop Conditions

- Stop and open a fresh source-truth or reviewer-facing catalog packet if
  alignment cannot be repaired without rerunning downloader/catalog workflows
  outside this packet's scope.
- Stop if reviewer-facing alignment would require weakening governed slot
  contracts, lowering coverage requirements, or deleting failing checks.
- Stop if the required changes cannot be staged without mixing unrelated dirty
  worktree edits.
- Stop if the only apparent path forward is to commit ignored
  `source_library/` artifacts without explicit user approval or a repository
  policy change.

## Local Commit Closeout Policy

- `complete-after-commit` rule: no milestone in this plan may be marked
  complete, `resolved`, or `reduced` until verification passes, durable
  docs/handoff updates land, and the local atomic commit exists. A verified
  but uncommitted slice is only ready-to-close.
- Stage only the verified blocker slice.
- Leave unrelated dirty or untracked files untouched.
- Commit implementation, tests, docs, and handoff updates for the completed
  milestone in one local atomic commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md` and the affected current
  route/state docs.
- Treat each milestone as incomplete until that commit exists.

## Residual Risks And Next Milestone Routing

- After this blocker clears, ECID and South Plateau may still fail on packet-local
  review artifacts such as compliance-review outputs, review packet rows,
  decision-support artifacts, or final-QA families. Those failures belong back
  to `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`.
- If reviewer-facing alignment requires a new governed reviewer-facing source
  set rather than a direct rebind to `source-set-f70ea11e04ae3d53`, record the
  new source-set identity and its creation command in the handoff before
  returning to replay repair.

## Closeout Checklist

- [ ] Milestone outcome label matches the governing verification signals.
- [ ] Reviewer-facing source-set truth is explicit and singular.
- [ ] Focused tests and replay-preflight commands were rerun and recorded.
- [ ] Top-level docs and handoff route to the same next truthful slice.
- [ ] `ruff check`, `git diff --check`, and plan lint passed.
- [ ] Only the verified milestone slice was staged and committed.
