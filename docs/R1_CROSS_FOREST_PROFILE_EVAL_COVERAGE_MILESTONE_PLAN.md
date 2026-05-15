# Region 1 Cross-Forest Profile Eval Coverage Milestone Plan

Date: 2026-05-13

Status: Proposed 2026-05-15 (Milestones 0-1 resolved and committed; Milestone 2 resolved and committed in `5aaa5d4`; Milestones 3-4 remain open)

Milestone 0 closeout summary on 2026-05-15:

- The predecessor seam is no longer a future dependency. `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`
  is now resolved on `2026-05-15`, and the live repo already carries the committed
  `phase-eval` direct-eval seam plus the upstream, downstream, gold, and real-package coverage
  consumers this plan expected.
- No equivalent cross-forest profile-eval producer, contract file, coverage-register row, or
  schema surface exists under a different live name. This plan is still the first owner of that
  lane.
- The active full-canonical source set for this lane remains `source-set-5e65d845ce77e1a0`.
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` does not expose a top-level
  `active_source_set_id`, so later verification must resolve active source-set truth from the
  current-state docs and source-set-specific readiness artifact paths instead of assuming that
  field exists.
- The live Region 1 roster still stands at `1` `covered`, `2` `fixture_contract_defined`, and `7`
  validated `not_started` profiles. The validated-but-`not_started` forest list is:
  `bitterroot-nf`,
  `dakota-prairie-grasslands`,
  `helena-lewis-and-clark-nf`,
  `idaho-panhandle-nfs`,
  `kootenai-nf`,
  `lolo-nf`, and
  `nez-perce-clearwater-nfs`.
- Milestone 3 execution order for the `7` tracking-only forests is now explicitly set from live
  inventory breadth and current-state evidence:
  `dakota-prairie-grasslands`,
  `helena-lewis-and-clark-nf`,
  `nez-perce-clearwater-nfs`,
  `idaho-panhandle-nfs`,
  `kootenai-nf`,
  `bitterroot-nf`,
  `lolo-nf`.
  This is eval-contract ordering only. It is not a reviewer-ready or live-package readiness claim.

Milestone 1 closeout summary on 2026-05-15:

- The repo now ships the first governed cross-forest profile-eval lane:
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `src/usfs_r1_ea_sources/forest_plan_profile_eval.py`,
  `tests/test_forest_plan_profile_eval_contracts.py`, and the public CLI command
  `forest-plan-profile-eval`.
- The Milestone 1 closeout checkpoint is local commit `46a2d49`
  (`eval: add cross-forest profile coverage gate`).
- The aggregate producer reads the live roster from
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` plus
  `config/forest_plan_profiles.json`. It does not keep a second hand-maintained forest list.
- The new readiness normalization is deliberately narrow: only the already-covered or
  fixture-defined rows now carry explicit `fixture_family_ids`, so the aggregate lane can measure
  live roster metadata instead of silently inferring families in code.
- The first live replay is intentionally red and fail-closed on the active full-canonical source
  set `source-set-5e65d845ce77e1a0`: `covered=1`, `fixture_contract_defined=2`, `not_started=7`,
  and `profile_failure_count=9`.
- Custer Gallatin is the only passing profile under the new gate. Beaverhead-Deerlodge and
  Flathead now fail only on coverage status, while the seven tracking-only forests fail on status,
  positive-count, hard-negative-count, and missing-fixture-family floors.
- Milestone 2 is now the next executable slice in this packet: promote Beaverhead and Flathead
  from thin fixture contracts to real `covered` status under this aggregate gate.

Milestone 2 closeout summary on 2026-05-15:

- Beaverhead-Deerlodge and Flathead now satisfy the Milestone 2 richer floor in both the live
  readiness roster and the governed aggregate manifest:
  `minimum_positive_case_count >= 4`,
  `minimum_hard_negative_case_count >= 3`,
  and `minimum_selected_profile_compliance_case_count >= 1`.
- The Milestone 2 closeout checkpoint is local commit `5aaa5d4`
  (`eval: promote beaverhead and flathead profile coverage`).
- `config/region1_forest_plan_readiness_nepa_3d_v1.json` now marks both added active profiles as
  `covered` rather than `fixture_contract_defined`, and each row now carries explicit richer
  `fixture_family_ids` for scope, management-area or overlay, supporting-route or currentness,
  Custer hard negative, non-selected non-Custer hard negative, and selected-profile compliance.
- Focused selected-profile resolver coverage now exists for Beaverhead-Deerlodge and Flathead
  across positive scope/context cases, explicit supporting-route or currentness-positive cases,
  Custer hard negatives, sibling non-Custer hard negatives, and broad-trigger hard negatives, while
  the selected-profile compliance proofs remain green in `tests/test_compliance_review.py`.
- The live aggregate replay stays intentionally red on `source-set-5e65d845ce77e1a0`, but it has
  moved to the Milestone 2 expected state:
  `covered=3`,
  `fixture_contract_defined=0`,
  `not_started=7`,
  and `profile_failure_count=7`.
  Custer Gallatin, Beaverhead-Deerlodge, and Flathead now pass the governed lane; only the seven
  tracking-only profiles remain below floor.
- Milestone 3 is now the next executable slice in this packet: eliminate `not_started` across the
  seven validated tracking-only profiles without widening this lane into a reviewer-ready or
  live-package expansion claim.

Owner context: This is a fresh standalone follow-on milestone plan. It does not reopen
`docs/R1_MULTI_FOREST_PROFILE_EXPANSION_MILESTONE_PLAN.md`, which remains retired as a routing
note. Its predecessor `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` is now resolved and
committed, so later milestones in this plan may proceed from the refreshed Milestone 0 baseline
rather than waiting on that seam. Because that phase-eval milestone itself depends on the
real-package coverage,
gold-coverage, downstream direct-eval, and upstream evaluation-coverage milestones, this plan
assumes the earlier chain already delivered the evaluation coverage register, the real-package
coverage route for declared review contracts, and the direct-eval-aware `phase-eval` seam. If
those predecessor closeouts land equivalent artifacts under different names, Milestone 0 of this
plan must refresh the routing before code changes begin rather than recreating the same ownership
under new names.

## Purpose

Close the gap between Region 1 forest-plan profile readiness tracking and actual cross-forest
evaluation coverage.

Today the repo has broad roster visibility:

- all `10` Region 1 forest-plan profiles are configured in tracked config;
- all `10` profile inventories are validated on the active full-canonical source set; and
- the graph/readiness surfaces make the roster visible.

The weakness is that evaluation protection still sits on a narrow proving slice:

- Custer Gallatin is the only profile marked `covered`;
- Beaverhead-Deerlodge and Flathead are still only
  `applicability_eval_coverage.status="fixture_contract_defined"` with `1` positive and `1`
  hard-negative fixture each; and
- the remaining `7` validated tracking-only profiles still report
  `applicability_eval_coverage.status="not_started"`.

That means future resolver, profile-selection, and selected-profile compliance changes can regress
outside the current proving slices without tripping a governed cross-forest eval contract.

This milestone exists to convert Region 1 cross-forest profile coverage into an explicit direct-eval
lane: every validated profile gets governed fixture coverage, the thin Beaverhead/Flathead slices
become real covered contracts, and the resulting aggregate summary becomes part of the repo's
evaluation coverage and promotion routing.

This milestone is not complete until the cross-forest profile eval contract, per-profile fixture
coverage, aggregate eval gate, phase-eval/promotion wiring, docs, handoff updates, and one local
atomic commit per milestone all land together. A verified but uncommitted slice is only
ready-to-close.

## Dependency And Milestone 0 Refresh Rule

- Predecessor condition satisfied on `2026-05-15`:
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` is resolved and committed.
- If the phase-eval milestone lands its direct-eval manifest, coverage helper, or promotion wiring
  under different names, Milestone 0 must adopt those artifacts and rewrite this plan's later
  commands before implementation continues.
- If the predecessor milestone already introduces a generic producer slot for cross-forest profile
  eval summaries, Milestone 0 must reuse it rather than adding a second detached readiness lane.
- If the live Region 1 readiness roster, active source set, or profile coverage statuses drift
  before implementation starts, Milestone 0 must refresh the target counts and forest order before
  code changes begin.
- This plan is roster-wide only for evaluation coverage. It must not silently broaden into a
  roster-wide reviewer-ready or live-package expansion claim.

## Current Evidence

- `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` is now resolved on `2026-05-15`, and its
  closeout note says the next follow-on packet is this plan's Milestone 0 rather than a reopened
  direct-eval seam.
- The active full-canonical source set in `README.md` and `docs/CURRENT_SYSTEM_STATE.md` remains
  `source-set-5e65d845ce77e1a0`.
- `config/region1_forest_plan_readiness_nepa_3d_v1.json` currently records:
  - `custer-gallatin-nf` as `applicability_eval_coverage.status="covered"` with
    `positive_case_count=23` and `hard_negative_case_count=12`;
  - `beaverhead-deerlodge-nf` as `fixture_contract_defined` with `positive_case_count=1` and
    `hard_negative_case_count=1`;
  - `flathead-nf` as `fixture_contract_defined` with `positive_case_count=1` and
    `hard_negative_case_count=1`; and
  - `bitterroot-nf`, `dakota-prairie-grasslands`, `helena-lewis-and-clark-nf`,
    `idaho-panhandle-nfs`, `kootenai-nf`, `lolo-nf`, and `nez-perce-clearwater-nfs` as
    `not_started` even though each of those rows already has
    `component_inventory_validation.status="validated"`.
- The live roster therefore stands at `1` `covered`, `2` `fixture_contract_defined`, and `7`
  `not_started` profiles.
- `config/forest_plan_profiles.json` already carries explicit profile entries for all `10` tracked
  units, so the coverage gap is not missing profile identities; it is missing governed eval depth.
- `README.md` and `docs/CURRENT_SYSTEM_STATE.md` both say the remaining non-Custer profiles still
  need richer vocabulary and proving-review depth beyond the Beaverhead and Flathead reference
  slices.
- `tests/test_forest_plan_profiles.py` currently still locks Flathead's readiness row at
  `fixture_contract_defined` with `1` positive and `1` hard negative.
- `tests/test_nepa_knowledge_graph_export.py` currently treats
  `applicability_eval_coverage.status="fixture_contract_defined"` plus `1` positive / `1`
  hard-negative fixture as a sufficient graph-readiness surface for an added profile row.
- Beaverhead and Flathead do already have deeper selected-profile resolver and compliance unit-test
  slices in `tests/test_forest_plan_resolver.py` and `tests/test_compliance_review.py`, but those
  deeper slices are not yet normalized into one governed cross-forest eval contract.
- Milestone 1 now implements the first live `forest_plan_profile_eval` producer,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`, and the matching
  `docs/EVALUATION_COVERAGE_REGISTER.md` row. The lane is intentionally red until the later
  coverage-expansion milestones land.
- `docs/R1_MULTI_FOREST_PROFILE_EXPANSION_MILESTONE_PLAN.md` is retired and explicitly says future
  forest work should not widen back into a roster-wide implementation ask. This plan must stay
  evaluation-contract scoped rather than reviving that retired expansion mode.

## Goal

Resolve the scoped cross-forest evaluation-coverage weakness by making the Region 1 profile roster
governed by one explicit eval lane rather than by readiness metadata and a few isolated proving
tests.

Completion means all of the following are true:

- the repo has one tracked cross-forest profile eval contract and aggregate summary;
- no validated Region 1 profile remains `not_started`;
- Beaverhead-Deerlodge and Flathead are no longer allowed to stop at `1` positive and `1`
  hard-negative fixture each;
- every tracked profile has explicit positive and hard-negative evaluation fixtures tied to its
  configured profile data;
- the aggregate summary distinguishes baseline cross-forest coverage from reviewer-ready or
  live-package proof so the repo does not overclaim readiness; and
- the new lane is registered in the evaluation coverage register and wired into the
  direct-eval-aware `phase-eval` / promotion path where appropriate.

## Non-Goals

- Do not reopen the retired multi-forest implementation plan as a roster-wide reviewer-ready
  expansion project.
- Do not claim that all `10` profiles are live-package-proven or reviewer-ready just because all
  `10` have evaluation fixtures.
- Do not rewrite downloader, extraction, retrieval, authority selection, or real-package review
  logic unless the new cross-forest eval lane proves a real dependency.
- Do not weaken Beaverhead, Flathead, Custer Gallatin, phase-eval, promotion-suite, or graph
  validation gates to make the new lane pass.
- Do not stage ignored `source_library/` outputs unless repository policy changes.

## Scope

- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `config/forest_plan_profiles.json`
- new cross-forest profile eval contract config
- selected-profile resolver and compliance fixture coverage for Region 1 profiles
- one aggregate cross-forest profile eval command and result artifact
- phase-eval direct-eval contract extension for this producer lane
- evaluation coverage register, README, output schema, current-state, and handoff routing

## Out Of Scope

- turning every remaining Region 1 profile into a reviewer-ready live-package proving lane
- new source-delta capture or component parsing work unless Milestone 0 proves a real data gap
- bulk `source_library/` regeneration beyond bounded verification
- unrelated viewer work
- reintroducing a broad multi-forest implementation milestone instead of an evaluation-contract lane

## Owner Surfaces

- Cross-forest profile eval contract owner:
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `src/usfs_r1_ea_sources/forest_plan_profile_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`,
  `tests/test_forest_plan_profile_eval_contracts.py`
- Profile readiness and roster owner:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `config/forest_plan_profiles.json`,
  `src/usfs_r1_ea_sources/forest_plan_profiles.py`,
  `tests/test_forest_plan_profiles.py`
- Resolver and selected-profile fixture owner:
  `src/usfs_r1_ea_sources/forest_plan_resolver.py`,
  `tests/test_forest_plan_resolver.py`
- Selected-profile compliance fixture owner:
  `src/usfs_r1_ea_sources/compliance_review.py`,
  `tests/test_compliance_review.py`
- Graph/readiness and direct-eval routing owner:
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `src/usfs_r1_ea_sources/evidence_graph.py`,
  `config/phase_eval_direct_eval_v1.json`,
  `config/promotion_suite_v1.json`,
  `tests/test_nepa_knowledge_graph_export.py`,
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_promotion_suite.py`
- Docs and handoff owner:
  `README.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan

## Placement Rules

- Keep forest-specific knowledge in tracked config or test fixtures, not in new runtime
  `if forest_unit_id == ...` branches.
- Keep the new lane as an evaluation producer under `cli_eval.py`; do not hide it as a graph-only
  status field inside `nepa_knowledge_graph_export.py`.
- Treat `config/region1_forest_plan_readiness_nepa_3d_v1.json` as the roster/status authority and
  `config/forest_plan_profiles.json` as the runtime profile authority. The aggregate eval lane must
  consume those sources rather than creating a third hand-maintained forest roster.
- Preserve the distinction between:
  - `covered` evaluation coverage,
  - reviewer-ready selected-profile proof, and
  - live-package proof.
  The new lane may strengthen eval coverage across all profiles, but it must not upgrade readiness
  semantics without the separate forest-specific proving work.
- Do not widen the retired multi-forest expansion doc back into active implementation ownership.
  Any future forest-specific reviewer-ready or live-package work still belongs in its own forest
  milestone doc.

## Weak-Point Prevention Contract

- Weak point forecast: graph-ready or configured profiles still outrun eval coverage, so the roster
  looks complete while most profiles remain unprotected.
  Owner surface: `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `tests/test_forest_plan_profile_eval_contracts.py`
  Prevention gate: the aggregate eval contract must require `not_started_profile_count = 0` for all
  validated profiles and must fail if any validated profile remains outside the governed fixture
  lane.
  Fail threshold: the aggregate eval passes while any validated profile still reports
  `applicability_eval_coverage.status="not_started"`.
  Controlled violation: leave one validated profile such as `kootenai-nf` at `not_started`; the
  contract must fail.
  Future-Codex misuse scenario: a later session adds more runtime profile data but no eval fixtures;
  the aggregate gate must fail closed.

- Weak point forecast: Beaverhead and Flathead keep their current `1` positive / `1` hard-negative
  placeholder contracts and still count as "covered enough."
  Owner surface: `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `tests/test_forest_plan_profiles.py`,
  `tests/test_forest_plan_profile_eval_contracts.py`
  Prevention gate: every `active_profile_added_milestone_5` row must meet a richer floor:
  `positive_case_count >= 4`, `hard_negative_case_count >= 3`, and
  `selected_profile_compliance_case_count >= 1`.
  Fail threshold: Beaverhead or Flathead is still marked `fixture_contract_defined`, or is marked
  `covered` without those minimum counts.
  Controlled violation: keep Flathead at `1` positive and `1` hard negative; the contract must
  fail.
  Future-Codex misuse scenario: a later session renames the status to `covered` without adding
  broader fixtures; the richer-count gate must fail.

- Weak point forecast: the remaining tracking-only profiles get only one trivial positive and one
  Custer hard negative, which still leaves sibling-profile confusion and support-route drift
  untested.
  Owner surface: `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `tests/test_forest_plan_resolver.py`,
  `tests/test_forest_plan_profile_eval_contracts.py`
  Prevention gate: every `region1_tracking_only` profile must meet at least
  `positive_case_count >= 2` and `hard_negative_case_count >= 2`, with one non-selected
  non-Custer hard negative once another non-Custer covered profile exists.
  Fail threshold: a tracking-only profile is marked `covered` with only one positive and one
  Custer-only hard negative.
  Controlled violation: give `bitterroot-nf` only one positive and one Custer hard negative; the
  aggregate contract must fail.
  Future-Codex misuse scenario: a later session adds the easiest possible fixtures for every
  tracking-only profile and claims tight coverage; sibling-isolation floors must fail the lane.

- Weak point forecast: the new lane turns into a detached report and never becomes part of the
  actual direct-eval or promotion path.
  Owner surface: `config/phase_eval_direct_eval_v1.json`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py`,
  `config/promotion_suite_v1.json`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`
  Prevention gate: once the producer lane exists, the evaluation register and phase-eval direct-eval
  contract must consume it for Region 1 roster claims, and promotion must fail if the producer
  summary is stale, missing, or below floor.
  Fail threshold: the new summary can fail while phase-eval or promotion still stays green for the
  relevant full-canonical roster claim.
  Controlled violation: set `not_started_profile_count=1` in a fixture summary while all other
  phase counts remain green; phase-eval/promotion tests must fail.
  Future-Codex misuse scenario: a later session updates only the standalone command and leaves
  routing unchanged; the direct-eval and promotion tests must fail before commit.

- Weak point forecast: this plan quietly reopens a broad multi-forest implementation program rather
  than staying evaluation-contract scoped.
  Owner surface: this plan, `docs/SESSION_HANDOFF.md`, `docs/CURRENT_SYSTEM_STATE.md`
  Prevention gate: every milestone closeout must preserve the distinction between cross-forest eval
  coverage and reviewer-ready/live-package proof.
  Fail threshold: closeout docs imply all profiles are reviewer-ready or live-package-proven
  because all profiles are eval-covered.
  Controlled violation: if docs say "all Region 1 profiles are reviewer-ready" after only fixture
  expansion, the milestone is not complete.
  Future-Codex misuse scenario: a later session uses the eval lane to overclaim readiness; doc and
  routing gates must catch the semantic drift.

## Milestone Sequence

### Milestone 0 - Post-Phase-Eval Preflight And Roster Baseline

Outcome label: reduced

Purpose: start this lane only after the predecessor direct-eval/phase-eval work is truly complete,
then rebaseline the live Region 1 roster and adjust the plan to the actual repo state before code
changes begin.

Implementation tasks:

1. Verify the predecessor chain exists and is green:
   - `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md` is closed and committed
   - the required upstream, downstream, gold, and real-package predecessor artifacts from that plan
     exist under their implemented names
   - the direct-eval-aware `phase-eval` route exists and can accept new producer lanes
2. Rebaseline the current Region 1 roster from live repo artifacts:
   - active source set
   - `profile_kind` counts
   - `covered`, `fixture_contract_defined`, and `not_started` counts
   - exact validated-but-`not_started` forest list
3. Confirm whether any predecessor milestone already created equivalent cross-forest eval artifacts,
   contract slots, or register rows under different names.
4. If the live roster or predecessor wiring drifted, update this plan, the handoff note, and the
   later verification commands before Milestone 1 begins.
5. Select the execution order for the `7` tracking-only forests from live evidence, but keep this
   as eval-contract ordering only. Do not convert that order into a reviewer-ready claim.

Acceptance criteria:

- This plan or its Milestone 0 closeout note records the exact current roster counts and the exact
  validated-but-`not_started` forest list.
- Later milestones do not duplicate predecessor artifacts under new names.
- If the live system drifted, the plan is rewritten before implementation continues.

Verification:

```bash
git status -sb
rg -n "Status: Resolved|next follow-on packet|Milestone 0" docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md
python - <<'PY'
import json
import re
from pathlib import Path
obj = json.loads(Path('config/region1_forest_plan_readiness_nepa_3d_v1.json').read_text())
rows = obj['profile_rows']
status_counts = {}
profile_kind_counts = {}
active_source_sets = set()
validated_not_started = []
for row in rows:
    status = row.get('applicability_eval_coverage', {}).get('status', 'missing')
    profile_kind = row.get('profile_kind', 'missing')
    status_counts[status] = status_counts.get(status, 0) + 1
    profile_kind_counts[profile_kind] = profile_kind_counts.get(profile_kind, 0) + 1
    if status == 'not_started' and row.get('component_inventory_validation', {}).get('status') == 'validated':
        validated_not_started.append(row['forest_unit_id'])
    artifact_path = row.get('component_inventory_validation', {}).get('artifact_path', '')
    match = re.search(r'(source-set-[^/]+)', artifact_path)
    if match:
        active_source_sets.add(match.group(1))
print(status_counts)
print(profile_kind_counts)
print(validated_not_started)
print(sorted(active_source_sets))
PY
rg -n "phase-eval|direct-eval|profile eval|forest-plan profile" README.md docs/CURRENT_SYSTEM_STATE.md docs/EVALUATION_COVERAGE_REGISTER.md docs/OUTPUT_SCHEMAS.md
rg -n "forest_plan_profile_eval|region1_forest_plan_profile_eval_coverage_v1|cross-forest profile eval" README.md docs/CURRENT_SYSTEM_STATE.md docs/EVALUATION_COVERAGE_REGISTER.md docs/OUTPUT_SCHEMAS.md src tests config
```

Docs and handoff updates required before closeout:

- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 0 stop conditions:

- The predecessor phase-eval/direct-eval milestone is not actually complete.
- The live roster or predecessor artifact names drifted and the plan has not been refreshed.
- The only way to proceed is to duplicate the roster or direct-eval routing by hand instead of
  consuming predecessor ownership.

### Milestone 1 - Add The Cross-Forest Profile Eval Contract And Aggregate Gate

Outcome label: resolved

Purpose: create one governed producer lane for Region 1 profile coverage instead of leaving this
state spread across readiness JSON, graph export metadata, and isolated forest-specific tests.

Implementation tasks:

1. Add `config/region1_forest_plan_profile_eval_coverage_v1.json` with:
   - `schema_version`
   - `contract_id`
   - active source-set binding or freshness expectations
   - all `10` tracked `forest_unit_id` values
   - per-profile `profile_kind`
   - per-profile coverage floors and required fixture families
   - aggregate required counts:
     - `covered_profile_count = 10`
     - `fixture_contract_defined_profile_count = 0`
     - `not_started_profile_count = 0`
2. Add a focused producer module such as
   `src/usfs_r1_ea_sources/forest_plan_profile_eval.py` plus a `cli_eval.py` entry point such as
   `forest-plan-profile-eval`.
3. Make the producer read the roster from `config/region1_forest_plan_readiness_nepa_3d_v1.json`
   and `config/forest_plan_profiles.json` rather than from a separate hand-maintained forest list.
4. Emit one aggregate summary artifact and one human-readable report under a governed
   `source_library/evaluations/` path.
5. Add `tests/test_forest_plan_profile_eval_contracts.py` proving missing roster rows, duplicated
   profile IDs, missing floors, or mismatched readiness/profile roster identities fail closed.

Acceptance criteria:

- The repo has one explicit cross-forest profile eval contract and aggregate producer lane.
- The contract reads the tracked readiness/profile roster instead of inventing a second forest list.
- The aggregate contract fails when any profile remains below the declared coverage floor.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profile_eval_contracts.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Docs and handoff updates required before closeout:

- `docs/EVALUATION_COVERAGE_REGISTER.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 1 stop conditions:

- The producer can only work by maintaining a second manual forest roster.
- The producer can only summarize readiness metadata without enforcing explicit fixture floors.

### Milestone 2 - Promote Beaverhead And Flathead From Thin Fixture Contracts To Covered

Outcome label: resolved

Purpose: remove the current false comfort that Beaverhead and Flathead are "good enough" with only
one positive and one hard-negative fixture each.

Implementation tasks:

1. Expand Beaverhead and Flathead fixture coverage so each added active profile records at least:
   - `positive_case_count >= 4`
   - `hard_negative_case_count >= 3`
   - `selected_profile_compliance_case_count >= 1`
2. Required coverage families for each added active profile must include:
   - scope-positive resolver evidence
   - overlay or management-area positive coverage
   - supporting-route or currentness positive coverage where the profile declares those routes
   - Custer Gallatin hard negative
   - non-selected non-Custer hard negative
   - one selected-profile compliance proof
3. Update `config/region1_forest_plan_readiness_nepa_3d_v1.json` so Beaverhead and Flathead can no
   longer remain `fixture_contract_defined`.
4. Normalize the richer Beaverhead and Flathead slices into the aggregate producer rather than
   leaving them as ad hoc deeper tests only.

Acceptance criteria:

- Beaverhead and Flathead are both `covered`, not `fixture_contract_defined`.
- Each meets the richer count floors and required coverage families above.
- The aggregate producer fails if either profile drops back to a `1` positive / `1` hard-negative
  placeholder contract.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_forest_plan_profile_eval_contracts.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json
git diff --check
```

Docs and handoff updates required before closeout:

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 2 stop conditions:

- Beaverhead or Flathead is relabeled `covered` without meeting the richer-count floor.
- The only new negatives remain Custer-only negatives and never test sibling non-Custer confusion.

### Milestone 3 - Eliminate `not_started` Across The Seven Validated Tracking-Only Profiles

Outcome label: resolved

Purpose: ensure every validated Region 1 profile has governed evaluation protection, even when it
is not yet a reviewer-ready or live-package proving slice.

Implementation tasks:

1. For each validated tracking-only profile:
   - `bitterroot-nf`
   - `dakota-prairie-grasslands`
   - `helena-lewis-and-clark-nf`
   - `idaho-panhandle-nfs`
   - `kootenai-nf`
   - `lolo-nf`
   - `nez-perce-clearwater-nfs`
   add explicit positive and hard-negative fixture coverage driven by the configured profile data.
2. Each tracking-only profile must meet at least:
   - `positive_case_count >= 2`
   - `hard_negative_case_count >= 2`
   - one scope-positive resolver fixture
   - one hard negative from a non-selected forest once another non-Custer covered profile exists
3. Keep these fixtures evaluation-scoped. Do not imply selected-profile compliance reviewer-ready
   proof or live-package proof for tracking-only profiles unless a separate forest-specific
   milestone supplies that depth.
4. Update `config/region1_forest_plan_readiness_nepa_3d_v1.json` so no validated profile remains
   `not_started`.
5. Extend graph/readiness tests so graph promotion cannot continue to rely on `not_started` or thin
   placeholder coverage for validated profiles.

Acceptance criteria:

- All `7` currently validated tracking-only profiles are no longer `not_started`.
- Every tracked Region 1 profile is `covered` by the end of this milestone.
- The aggregate producer fails if any validated profile remains outside the governed fixture lane.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_forest_plan_profile_eval_contracts.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id <active-source-set-id>
git diff --check
```

Docs and handoff updates required before closeout:

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 3 stop conditions:

- Any tracking-only profile can only be lifted by inventing runtime branches instead of config- and
  fixture-backed coverage.
- The only way to clear a tracking-only profile is to weaken its floor below `2` positives and `2`
  hard negatives.

### Milestone 4 - Wire The New Lane Into Phase-Eval, Promotion, And Coverage Routing

Outcome label: resolved

Purpose: make the new cross-forest profile producer a governed system input rather than a detached
report.

Implementation tasks:

1. Extend `config/phase_eval_direct_eval_v1.json` and the normalized direct-eval loader so the new
   producer summary is a required direct-eval input for the full-canonical Region 1 roster claim.
2. Update `evidence_graph.py` / `phase_eval_direct_eval.py` so source-set `phase-eval` records the
   new lane's identity, counts, and failure reasons.
3. Extend `config/promotion_suite_v1.json` so the relevant full-canonical claim fails when the
   cross-forest profile eval summary is missing, stale, or below floor.
4. Add the new row to `docs/EVALUATION_COVERAGE_REGISTER.md` and document:
   - what the producer covers
   - what `covered` means in this lane
   - what it does not mean for reviewer-ready or live-package proof
5. Update `README.md`, `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
   `docs/SESSION_HANDOFF.md` so future sessions know the roster is eval-covered without overstating
   operational readiness.

Acceptance criteria:

- The evaluation coverage register has an explicit cross-forest profile eval row.
- Phase-eval and promotion can no longer ignore a failed or stale cross-forest profile producer.
- Docs preserve the distinction between eval coverage, reviewer-ready proof, and live-package proof.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profile_eval_contracts.py tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_promotion_suite.py tests/test_nepa_knowledge_graph_export.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
git diff --check
```

Docs and handoff updates required before closeout:

- `README.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Milestone 4 stop conditions:

- The new producer can fail while phase-eval or promotion still stays green for the same
  full-canonical roster claim.
- Closeout docs blur eval coverage into reviewer-ready or live-package readiness.

## Required Implementation Artifacts

- `config/region1_forest_plan_profile_eval_coverage_v1.json`
- `src/usfs_r1_ea_sources/forest_plan_profile_eval.py`
- focused `cli_eval.py` registration for `forest-plan-profile-eval`
- `tests/test_forest_plan_profile_eval_contracts.py`
- focused updates to:
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `tests/test_forest_plan_profiles.py`,
  `tests/test_forest_plan_resolver.py`,
  `tests/test_compliance_review.py`,
  `tests/test_nepa_knowledge_graph_export.py`,
  `config/phase_eval_direct_eval_v1.json`,
  `tests/test_phase_eval_direct_eval_contracts.py`,
  `tests/test_evidence_graph.py`,
  `config/promotion_suite_v1.json`,
  `tests/test_promotion_suite.py`

## Required Documentation And Handoff Updates

- `README.md`
  document the new cross-forest profile eval lane and preserve the distinction between eval
  coverage and reviewer-ready or live-package proof
- `docs/OUTPUT_SCHEMAS.md`
  define the new producer contract, result schema, per-profile coverage fields, and aggregate counts
- `docs/EVALUATION_COVERAGE_REGISTER.md`
  add the cross-forest profile eval row and its direct-eval status
- `docs/CURRENT_SYSTEM_STATE.md`
  update the live profile coverage counts and explain what the new lane does and does not prove
- `docs/SESSION_HANDOFF.md`
  route the next session to the first incomplete milestone and record any remaining uncovered
  profile or readiness-semantics gaps
- this milestone plan with implementation status and closeout evidence

## Required Verification Gates

Minimum closeout gates for the full milestone:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profile_eval_contracts.py tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_nepa_knowledge_graph_export.py tests/test_phase_eval_direct_eval_contracts.py tests/test_evidence_graph.py tests/test_promotion_suite.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id <active-source-set-id> --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --source-set-id <active-source-set-id>
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
git diff --check
```

If predecessor milestones publish the needed direct-eval or promotion artifacts under different
commands or paths than this plan currently names, Milestone 0 must update the closeout commands in
`docs/SESSION_HANDOFF.md` before implementation continues.

## Verification And Anti-Weakening Rules

- Do not weaken tests, evals, or gates just to make cross-forest coverage go green. Any replacement
  coverage must be equivalent or stronger, and the closeout evidence must prove coverage did not get
  easier.
- Do not get this milestone green by relabeling `fixture_contract_defined` or `not_started` rows as
  `covered` without meeting the declared count floors.
- Do not get this milestone green by turning reviewer-ready or live-package semantics into mere
  fixture coverage.
- When tests, evals, or gates change, add negative or controlled-violation coverage showing the new
  lane is harder to fake, not easier to pass.
- For code milestones, run focused tests, `tests/test_architecture_contract.py`, `ruff check src
  tests`, `python -m compileall src`, and `git diff --check`.
- For live roster claims, replay only the bounded full-canonical commands named above. Do not rerun
  downloader or broad source capture unless Milestone 0 proves freshness cannot otherwise be
  established.

## Acceptance Criteria

- The repo has one explicit Region 1 cross-forest profile eval contract and aggregate summary.
- No validated Region 1 profile remains `not_started`.
- Beaverhead and Flathead no longer stop at a `1` positive / `1` hard-negative placeholder
  contract.
- Every tracked Region 1 profile is `covered` by explicit positive and hard-negative fixture
  coverage tied to its configured profile data.
- The new lane is registered in the evaluation coverage register and wired into the
  direct-eval-aware phase-eval/promotion path where appropriate.
- No closeout may reduce any declared per-profile floor, remove a required negative case family, or
  drop an existing resolver, compliance, graph, phase-eval, or promotion gate just to make the new
  lane pass.

## Commit Policy

- Complete one local atomic commit per milestone after that milestone's verification passes.
- Stage only the verified slice for that milestone: code, tests, config, docs, and any tracked
  helper artifacts needed to explain the change.
- Do not stage ignored `source_library/` outputs unless repository policy changes.
- If a milestone reaches verified code and docs but is not yet committed, report it as
  ready-to-close, not complete.

## Stop Conditions

- The predecessor phase-eval/direct-eval milestone is not actually complete.
- The only path to green is to duplicate the roster in a second config file or to weaken coverage
  floors below the declared minimums.
- The only path to green is to blur eval coverage into reviewer-ready or live-package readiness.
- The new lane cannot be wired into phase-eval or promotion without creating a second detached
  readiness path.
