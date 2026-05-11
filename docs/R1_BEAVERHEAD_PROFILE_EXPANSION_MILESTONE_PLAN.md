# Region 1 Beaverhead-Deerlodge Profile Expansion Milestone Plan

Date: 2026-05-11
Status: implemented reference slice
Owner context: single-forest post-V1 expansion milestone for Beaverhead-Deerlodge, retained as the
reference pattern for future one-forest-at-a-time profile expansion work

## Purpose

The multi-forest expansion plan was too broad for clean execution. This milestone rewrites that lane
into the atomic single-forest shape that future Region 1 expansion work should follow.

Beaverhead-Deerlodge is the correct reference slice because it is already the first non-Custer
profile proven to reviewer-ready depth. This plan documents the exact milestone boundary, gates,
owner surfaces, and closeout contract that future forest-specific milestones must copy rather than
reopening a roster-wide plan.

This document is a reference closeout artifact, not the next active implementation plan. Future
post-V1 expansion work should open a new forest-specific milestone file that copies this contract
instead of extending Beaverhead's artifact.

## Current Evidence

- `docs/CURRENT_SYSTEM_STATE.md` says the active full-canonical source set is
  `source-set-5e65d845ce77e1a0`, all `10` tracked forest plans validate in the live inventory, and
  Beaverhead-Deerlodge is the first non-Custer reviewer-ready depth slice.
- `docs/SESSION_HANDOFF.md` records that Beaverhead-Deerlodge already carries district, landscape,
  management-area, overlay, and supporting-route vocabulary grounded in active local support
  records, and that explicit selected-profile compliance review is now strict for Beaverhead.
- `config/forest_plan_profiles.json` shows the Beaverhead-Deerlodge profile as the only
  non-Custer profile besides Custer Gallatin that currently has non-empty district, geographic-area,
  management-area, overlay, and supporting-trigger data.
- Focused tests already prove the Beaverhead slice in code:
  `tests/test_forest_plan_profiles.py`, `tests/test_forest_plan_resolver.py`,
  `tests/test_compliance_review.py`, `tests/test_cli.py`, and
  `tests/test_architecture_contract.py`.
- The live all-R1 inventory proof already exists and remains mandatory for closeout discipline:
  `forest-plan-components-build --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  validates all `10` tracked forest plans on `source-set-5e65d845ce77e1a0`.

## Goal

Preserve a durable, executable, single-forest milestone contract for Beaverhead-Deerlodge that:

- proves one forest can be expanded to reviewer-ready depth without weakening the default Custer
  path;
- locks in the gate-first sequence future forests must follow one at a time; and
- keeps live all-R1 forest-plan verification as a mandatory closeout gate even for a single-forest
  milestone.

## Non-Goals

- Do not widen this plan back into a multi-forest roster implementation ask.
- Do not reopen downloader, catalog, source-delta capture, extraction, parser recovery, or replay
  work unless a future forest-specific milestone proves a real dependency.
- Do not weaken default Custer Gallatin behavior, ambiguity handling, or out-of-scope handling to
  make a non-Custer forest appear ready.
- Do not stage or commit `source_library/` generated artifacts unless repository policy changes or
  the user explicitly expands scope.
- Do not treat Beaverhead as proof that every remaining forest is ready for the same treatment.

## Scope

- `config/forest_plan_profiles.json`
- `src/usfs_r1_ea_sources/forest_plan_profiles.py`
- `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `src/usfs_r1_ea_sources/compliance_review.py`
- `src/usfs_r1_ea_sources/compliance_review_eval.py`
- `src/usfs_r1_ea_sources/compliance_gold_eval.py`
- `src/usfs_r1_ea_sources/compliance_validation.py`
- `src/usfs_r1_ea_sources/cli_compliance.py`
- focused tests under `tests/test_forest_plan_profiles.py`,
  `tests/test_forest_plan_resolver.py`, `tests/test_compliance_review.py`,
  `tests/test_cli.py`, and `tests/test_architecture_contract.py`
- durable docs and handoff updates for this single-forest milestone

## Out Of Scope

- Bitterroot, Dakota Prairie, Flathead, Helena-Lewis-and-Clark, Idaho Panhandle, Kootenai, Lolo,
  or Nez Perce-Clearwater expansion work
- `source_library/` bulk regeneration
- workbook row edits
- unrelated viewer work
- East Crazies replay repairs
- new authority, applicability, or rule-pack milestones outside the Beaverhead profile lane

## Owner Surfaces

- Beaverhead profile data contract: `config/forest_plan_profiles.json`
- Profile parsing and validation: `src/usfs_r1_ea_sources/forest_plan_profiles.py`
- Beaverhead scope, area, overlay, and supporting-route resolution:
  `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- Beaverhead selected-profile compliance gate ownership:
  `src/usfs_r1_ea_sources/compliance_review.py`,
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  `src/usfs_r1_ea_sources/compliance_gold_eval.py`,
  `src/usfs_r1_ea_sources/compliance_validation.py`,
  `src/usfs_r1_ea_sources/cli_compliance.py`
- Regression and prevention surface:
  `tests/test_forest_plan_profiles.py`,
  `tests/test_forest_plan_resolver.py`,
  `tests/test_compliance_review.py`,
  `tests/test_cli.py`,
  `tests/test_architecture_contract.py`
- Status routing: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, this plan, and
  `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep Beaverhead-specific knowledge in `config/forest_plan_profiles.json`, not in new runtime
  branches.
- Keep runtime logic generic and profile-driven. Do not add `if forest_unit_id == "beaverhead-..."`
  control flow unless the logic is reusable and config-backed.
- Preserve the existing default Custer path and Beaverhead-selected path together; new forest work
  must clone this milestone into a new plan file instead of editing Beaverhead rules in place.
- Future forest-specific milestone plans should follow the same sequence and closeout contract used
  here, with only the forest-specific owner surfaces, fixtures, and evidence swapped.

## Weak-Point Prevention Contract

### Weak point 1: Beaverhead becomes a stealth multi-forest milestone again

- Weak point forecast: future edits may quietly add Bitterroot or another forest to this artifact
  instead of opening a new forest-specific plan.
- Owner surface: this plan, `docs/SESSION_HANDOFF.md`
- Prevention gate: doc review plus `git diff --check`
- Fail threshold: this plan or its acceptance criteria starts naming multiple new target forests
  instead of Beaverhead only
- Controlled violation: the retired multi-forest plan file stays in place as a routing note, so a
  future session can distinguish the old broad plan from the intended single-forest pattern
- Future-Codex misuse scenario: a future session appends another forest to Beaverhead's plan to
  save time; this plan prevents that by defining Beaverhead as a closed reference slice and routing
  each later forest to its own milestone doc

### Weak point 2: Runtime logic drifts back into forest-specific code branches

- Weak point forecast: future edits may bypass `config/forest_plan_profiles.json` and encode
  Beaverhead handling directly in Python.
- Owner surface: `forest_plan_profiles.py`, `forest_plan_resolver.py`, `compliance_review.py`
- Prevention gate: focused profile, resolver, compliance, CLI, and architecture-contract tests
- Fail threshold: Beaverhead behavior requires a dedicated Python branch because the config cannot
  express it
- Controlled violation: retain negative tests proving unselected profiles remain out-of-scope even
  when their names appear in package text
- Future-Codex misuse scenario: a future session patches one Beaverhead corner case with a direct
  runtime exception path; this milestone requires the behavior to stay profile-backed

### Weak point 3: Trigger overmatch creates false Beaverhead supporting evidence

- Weak point forecast: broad FEIS, ROD, BA, or BO terms may resolve Beaverhead support records
  without explicit package cues.
- Owner surface: `config/forest_plan_profiles.json`, `forest_plan_resolver.py`,
  `tests/test_forest_plan_resolver.py`
- Prevention gate: Beaverhead resolver positive and negative trigger tests
- Fail threshold: generic section labels, lowercase acronyms, or background-only references resolve
  supporting-plan evidence that should remain unresolved
- Controlled violation: keep explicit negative fixtures for generic decision labels, generic
  purpose-and-need terms, lowercase acronyms, and background-only district mentions
- Future-Codex misuse scenario: a future session broadens Beaverhead trigger terms to make another
  forest easier; this milestone preserves fail-closed Beaverhead trigger coverage

### Weak point 4: Beaverhead appears complete while a mandatory vocabulary class is empty

- Weak point forecast: a future edit could preserve forest-unit names and source roles but lose a
  required Beaverhead category such as districts, geographic areas, management areas, overlays, or
  supporting routes.
- Owner surface: `config/forest_plan_profiles.json`, `tests/test_forest_plan_profiles.py`
- Prevention gate: Beaverhead profile completeness assertions
- Fail threshold: the Beaverhead profile has an empty required vocabulary or trigger array
- Controlled violation: profile tests fail if Beaverhead loses district, geographic-area,
  management-area, overlay, or supporting-route data
- Future-Codex misuse scenario: a future session trims Beaverhead data during another refactor and
  still claims the profile is reviewer-ready; this milestone keeps category-complete assertions in
  the focused profile test surface

### Weak point 5: The compliance gate becomes weaker while broadening beyond Custer

- Weak point forecast: the selected-profile forest-plan reviewer-ready gate may stop requiring
  component/adjudication evidence for Beaverhead.
- Owner surface: `compliance_validation.py`, `tests/test_compliance_review.py`
- Prevention gate: Beaverhead selected-profile compliance-review regressions plus CLI and
  architecture-contract coverage
- Fail threshold: a Beaverhead-selected compliance review passes while its forest-plan component
  gate is unresolved or missing
- Controlled violation: keep unit tests where Beaverhead lacks matching component or adjudication
  evidence and must fail closed
- Future-Codex misuse scenario: a future session loosens non-Custer gate requirements to support a
  later forest; this milestone preserves Beaverhead parity as the minimum contract

### Weak point 6: A single-forest milestone closes without live all-R1 verification

- Weak point forecast: future forest-specific work may close from Beaverhead-only fixtures without
  replaying the live all-R1 inventory proof.
- Owner surface: `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`
- Prevention gate: mandatory live `forest-plan-components-build` replay before closeout
- Fail threshold: the all-R1 inventory command does not validate all `10` tracked forest plans on
  the active full-canonical source set at closeout time
- Controlled violation: if the active source set drifts or any profile build fails, stop the
  milestone and reroute to the blocker instead of committing a partial single-forest closeout
- Future-Codex misuse scenario: a future session claims a forest-specific milestone is done from
  unit fixtures only; this plan preserves the live all-R1 closeout requirement

## Milestone Sequence

### Sequence 0: Add the Beaverhead completeness contract

Outcome label: resolved

- Add or tighten tests that define what reviewer-ready Beaverhead profile depth means.
- Require Beaverhead to carry non-empty district, geographic-area, management-area, overlay, and
  supporting-route arrays.
- Keep the completeness gate Beaverhead-specific; future forests must get their own tests in their
  own milestone plans.

Required implementation artifacts:

- Beaverhead profile completeness tests in `tests/test_forest_plan_profiles.py`
- if needed, helper assertions in `forest_plan_profiles.py` or test helpers only

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py`

### Sequence 1: Enrich the Beaverhead profile in tracked config

Outcome label: resolved

- Author Beaverhead district aliases, named landscapes, management-area vocabulary, overlays, and
  support-record trigger routes from active local corpus evidence.
- Keep every Beaverhead support record explicit in config.
- If a Beaverhead category is genuinely unsupported, record it as an explicit accepted gap with an
  owner and next routing rather than leaving it empty.

Required implementation artifacts:

- `config/forest_plan_profiles.json`
- if needed, small validation helpers in `forest_plan_profiles.py`

Required verification:

- `python -m json.tool config/forest_plan_profiles.json >/dev/null`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py`

### Sequence 2: Prove Beaverhead resolver behavior

Outcome label: resolved

- Add focused Beaverhead resolver fixtures covering positive and negative cases.
- Prove Beaverhead can:
  - resolve selected forest scope from package text
  - resolve at least one district or project-location signal
  - resolve at least one geographic area, management area, or overlay
  - route FEIS, ROD, and ESA support evidence only when explicit package cues exist
- Prove Beaverhead still fails closed on ambiguity, generic triggers, and unselected profile
  references.

Required implementation artifacts:

- `tests/test_forest_plan_resolver.py`
- only minimal generic resolver changes needed to support Beaverhead config-driven behavior

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py`

### Sequence 3: Prove Beaverhead compliance-gate parity

Outcome label: resolved

- Add compliance-review fixtures proving a Beaverhead-selected profile is gate-required and cannot
  pass without reviewer-ready component and adjudication evidence.
- Retain existing Custer proofs while adding Beaverhead selected-profile cases.
- Keep ambiguous and out-of-scope paths non-required.

Required implementation artifacts:

- `tests/test_compliance_review.py`
- `tests/test_cli.py`
- only generic compliance-path changes needed for Beaverhead selected-profile parity

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_cli.py tests/test_architecture_contract.py`

### Sequence 4: All-R1 verification and single-forest closeout

Outcome label: resolved for the Beaverhead profile-depth gap, reduced for the broader any-R1
expansion claim

- Re-run the live all-R1 forest-plan inventory verification on the active full-canonical source set
  before closing the Beaverhead milestone.
- Refresh current-state docs, this plan, and the session handoff with the actual post-closeout
  state and next routing.
- Route the next step to a new forest-specific plan file instead of expanding Beaverhead's artifact.

Required implementation artifacts:

- refreshed status docs only if the verified live state materially changed

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_cli.py tests/test_architecture_contract.py`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
- `git diff --check`

Closeout interpretation:

- This milestone is `resolved` only for the Beaverhead-Deerlodge profile-depth and selected-profile
  gate-parity issue.
- The broader post-V1 "any R1 EA package review" problem remains `reduced` until future
  forest-specific milestones and selected real-package proofs close their own gates.

## Required Documentation And Handoff Updates

Before milestone closeout, update as applicable:

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

The handoff update must record:

- the completed Beaverhead milestone name
- exact verification commands
- pass/fail counts
- the active source set used for all-R1 verification
- residual risks
- the next forest-specific milestone boundary
- the closing commit hash

## Required Verification Gates

Focused code and contract verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_architecture_contract.py`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_cli.py`

Repository hygiene:

- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`

Mandatory all-R1 forest-plan verification before closeout:

- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
- acceptance signal: the command must validate all `10` tracked Region 1 forest plans on the
  active full-canonical source set before the milestone can be called complete

Optional but recommended if any readiness surface changes:

- `PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0`
- `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`

## Acceptance Criteria

- Beaverhead-Deerlodge has explicit non-empty district, geographic-area, management-area, overlay,
  and supporting-route data in `config/forest_plan_profiles.json`, or any accepted gap is
  explicitly recorded and routed.
- Resolver tests prove Beaverhead selected-profile scope resolution, routed supporting evidence,
  and ambiguity or out-of-scope failures.
- Compliance-review tests prove Beaverhead selected-profile review keeps
  `forest_plan_component_gate_reviewer_ready` strict and cannot pass without reviewer-ready
  component and adjudication support.
- The default Custer path remains compatible and green.
- The all-R1 forest-plan verification command validates all `10` tracked forest plans on the
  active full-canonical source set before closeout.
- Durable docs and the session handoff reflect that Beaverhead is the completed reference slice and
  that the next forest must get a new plan file instead of widening this one.
- The milestone closes with one local atomic commit containing only the verified Beaverhead slice.

## Stop Conditions

- A needed Beaverhead vocabulary or trigger cannot be grounded in the active local corpus and would
  require unsupported guessing.
- Resolver or compliance broadening requires Beaverhead-specific runtime branching that cannot be
  expressed cleanly through config.
- The active source set or full-R1 inventory verification drifts in a way that reopens parser,
  extraction, or corpus-readiness work outside Beaverhead's boundary.
- Required verification fails.
- Unrelated dirty work cannot be safely separated from the Beaverhead slice.

## Local Commit Closeout Policy

- Stage only the verified Beaverhead milestone slice.
- Leave unrelated viewer changes, draft exports, and other dirty or untracked files alone.
- Include implementation, tests, plan updates, current-state updates, and handoff updates in the
  same local atomic commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the milestone as incomplete until that commit exists.

## Residual Risks And Next Routing

- Beaverhead is the completed single-forest reference slice, not proof that the remaining forests
  can be promoted without more corpus-backed vocabulary and proving work.
- Future forests may need their own support-document curation, adjudication, or resolver negatives
  before they can match Beaverhead depth.
- The next milestone should be a new forest-specific plan file for one selected non-Custer forest,
  using Beaverhead's sequence and gates as the baseline rather than widening this document.
