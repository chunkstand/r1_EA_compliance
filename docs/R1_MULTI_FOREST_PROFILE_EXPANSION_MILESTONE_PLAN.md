# Region 1 Multi-Forest Profile Expansion Milestone Plan

Date: 2026-05-11
Status: ready for implementation
Owner context: post-V1 expansion lane for profile-driven forest-plan review on the active full-canonical corpus

## Purpose

The active forest-plan inventory lane is green for all `10` tracked Region 1 units, and the
forest-plan review gate is no longer Custer-only. The remaining weakness is narrower: most
non-Custer resolver profiles still stop at source-record readiness and do not yet carry the
district, landscape, management-area, overlay, and supporting-route vocabulary needed for
reviewer-ready package review depth.

This milestone exists to resolve the profile-depth gap across the remaining Region 1 forest plans
while preserving the long-lived default Custer Gallatin contract and the newly proven
Beaverhead-Deerlodge path.

Broader "review an EA on any R1 forest" readiness is expected to be reduced, not fully resolved, by
this milestone unless the final verification proves the expanded profiles also hold up under
selected real-package reviews.

## Current Evidence

- `docs/CURRENT_SYSTEM_STATE.md` says the active full-canonical source set is
  `source-set-5e65d845ce77e1a0`, all `10` tracked forest plans now build validated component
  inventories, Beaverhead-Deerlodge is the first non-Custer reviewer-ready depth slice, and the
  next required implementation boundary is repeating Beaverhead-level profile depth across the
  remaining non-Custer forest units.
- `docs/SESSION_HANDOFF.md` routes the immediate next step to repeating the Beaverhead
  profile-depth pattern across the remaining non-Custer units, then proving those richer profiles
  through selected real package reviews.
- `config/forest_plan_profiles.json` now covers all `10` tracked readiness units, but only
  `custer-gallatin-nf` and `beaverhead-deerlodge-nf` currently carry richer district, area,
  overlay, and supporting-trigger data. The remaining non-Custer profiles still contain empty
  vocabulary/trigger arrays.
- The current all-R1 inventory proof already exists on the active full-canonical source set:
  `forest-plan-components-build --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  validates all `10` tracked forest plans on `source-set-5e65d845ce77e1a0`. This milestone must
  replay that same verification before closeout so profile-depth edits do not silently reopen a
  forest-plan build regression elsewhere in the roster.
- The current milestone boundary is no longer parser/component recovery. It is post-V1
  multi-forest forest-plan review expansion with explicit `forest_plan_reviewer_not_ready` risk.

## Goal

Resolve the tracked per-forest vocabulary and supporting-route gap for the remaining Region 1
forest-plan profiles, prove that explicit non-Custer profile selection keeps the compliance gate
strict, and close the milestone only after a full all-R1 forest-plan verification pass succeeds on
the active full-canonical source set.

## Non-Goals

- Do not reopen downloader, catalog, source-delta capture, extraction, or full-canonical parser
  recovery work unless verification proves a real dependency.
- Do not weaken default Custer Gallatin behavior, out-of-scope handling, or ambiguity handling to
  make more profiles appear ready.
- Do not stage or commit `source_library/` generated artifacts unless repository policy changes or
  the user explicitly expands scope.
- Do not claim full any-R1 EA reviewer readiness unless selected real-package proofs across the
  expanded roster actually pass.

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
  `tests/test_forest_plan_resolver.py`, `tests/test_compliance_review.py`, and
  `tests/test_architecture_contract.py`
- durable docs and handoff updates for the milestone

## Out Of Scope

- `source_library/` bulk regeneration
- workbook row edits
- unrelated viewer work
- East Crazies replay repairs
- new authority, applicability, or rule-pack milestones outside the forest-plan profile lane

## Owner Surfaces

- Profile data contract: `config/forest_plan_profiles.json`
- Profile parsing/validation: `src/usfs_r1_ea_sources/forest_plan_profiles.py`
- Resolver scope, area, overlay, and supporting-route behavior:
  `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- Compliance gate ownership:
  `src/usfs_r1_ea_sources/compliance_review.py`,
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  `src/usfs_r1_ea_sources/compliance_gold_eval.py`,
  `src/usfs_r1_ea_sources/compliance_validation.py`,
  `src/usfs_r1_ea_sources/cli_compliance.py`
- Cross-profile regression surface:
  `tests/test_forest_plan_profiles.py`,
  `tests/test_forest_plan_resolver.py`,
  `tests/test_compliance_review.py`
- Status routing: `docs/CURRENT_SYSTEM_STATE.md`, this milestone plan, and `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep forest-specific knowledge in `config/forest_plan_profiles.json`, not in new runtime
  branches.
- New profile-trigger logic must stay profile-driven and auditable. Do not add hard-coded
  per-forest `if forest_unit_id == ...` routing in compliance or resolver code unless the logic is
  strictly generic and config-backed.
- Extend tests by adding explicit positive and negative fixtures for each new profile slice. Do not
  replace Beaverhead/Custer proofs with weaker aggregate-only checks.
- Preserve current CLI names and default behavior. New parameters or stricter behavior must remain
  backwards compatible for the default Custer path.

## Weak-Point Prevention Contract

### Weak point 1: Runtime logic drifts back into forest-specific code branches

- Weak point forecast: future edits may bypass `config/forest_plan_profiles.json` and encode
  Bitterroot, Flathead, or other units directly in Python.
- Owner surface: `forest_plan_profiles.py`, `forest_plan_resolver.py`, `compliance_review.py`
- Prevention gate: focused profile/resolver/compliance tests plus architecture-contract coverage
- Fail threshold: a new forest-specific branch is required to pass tests because the profile config
  cannot express the behavior
- Controlled violation: add or retain a negative test showing an unselected profile remains
  out-of-scope even when its names appear in package text
- Future-Codex misuse scenario: a future session adds a one-off `elif forest_unit_id == ...`
  shortcut for one forest; this milestone prevents that by requiring profile-backed fixtures and
  config-driven terms for every new forest slice

### Weak point 2: Trigger overmatch creates false reviewer-ready supporting evidence

- Weak point forecast: broad FEIS, ROD, BA, or BO terms may resolve support records without an
  explicit package cue
- Owner surface: `config/forest_plan_profiles.json`, `forest_plan_resolver.py`,
  `tests/test_forest_plan_resolver.py`
- Prevention gate: resolver positive and negative trigger tests for each enriched profile family
- Fail threshold: a package with generic section labels, lowercase acronyms, or background-only
  references resolves supporting-plan evidence that should stay unresolved
- Controlled violation: explicit negative fixtures for generic "selected alternative", generic
  "purpose and need", lowercase acronyms, and background-only district mentions
- Future-Codex misuse scenario: a future session adds generic trigger terms to make a new profile
  look complete; this milestone requires source-backed, fail-closed trigger fixtures

### Weak point 3: A profile appears "complete" while still lacking mandatory vocabulary categories

- Weak point forecast: a profile could gain one or two terms and be treated as done even though
  district, area, overlay, or route coverage is still empty
- Owner surface: `config/forest_plan_profiles.json`, `tests/test_forest_plan_profiles.py`
- Prevention gate: roster-level completeness assertions for milestone-scoped profiles
- Fail threshold: a profile declared complete in docs still has empty required arrays for its
  milestone scope
- Controlled violation: profile tests fail if a milestone-targeted unit is missing district,
  geographic-area, management-area, overlay, or supporting-route terms
- Future-Codex misuse scenario: a future session updates docs to claim a profile is ready after
  adding only names and source roles; this milestone requires category-complete assertions for each
  targeted forest

### Weak point 4: The compliance gate becomes weaker while broadening beyond Custer

- Weak point forecast: the forest-plan reviewer-ready gate may stop requiring component/adjudication
  evidence for new in-scope profiles
- Owner surface: `compliance_validation.py`, `tests/test_compliance_review.py`
- Prevention gate: selected-profile compliance-review regressions for success, ambiguous, and
  out-of-scope cases
- Fail threshold: an explicitly selected in-scope non-Custer profile passes compliance review while
  its forest-plan component gate is unresolved or missing
- Controlled violation: unit tests where the selected non-Custer profile lacks matching component
  evidence or component-adjudication support and must fail closed
- Future-Codex misuse scenario: a future session broadens "required" logic with a permissive scope
  list that exempts most non-Custer profiles; this milestone requires in-scope selected-profile
  parity tests

### Weak point 5: All-R1 closeout is claimed without re-verifying all forest plans

- Weak point forecast: profile-depth work closes with only targeted-unit tests while another
  forest-plan inventory or readiness surface has drifted
- Owner surface: `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`, `docs/CURRENT_SYSTEM_STATE.md`
- Prevention gate: mandatory all-R1 forest-plan verification block before milestone closeout
- Fail threshold: `forest-plan-components-build --manifest-path ...` does not validate all
  `10` tracked forest plans on the active full-canonical source set at closeout time
- Controlled violation: if the active source set drifts or any profile build fails, stop the
  milestone and reroute to the blocker instead of committing a partial "all R1" claim
- Future-Codex misuse scenario: a future session closes the milestone from unit fixtures only; this
  milestone requires a live all-R1 verification replay before closeout

## Milestone Sequence

### Sequence 0: Add a roster-level profile-depth contract

Outcome label: resolved

- Add or tighten tests that define which remaining non-Custer profiles are in scope for this
  milestone and what "depth complete" means for each one.
- Require each milestone-targeted profile to carry non-empty district, geographic-area,
  management-area, overlay, and supporting-route arrays.
- Preserve a clear distinction between milestone-targeted profiles and intentionally deferred units
  if the work is split across multiple commits.

Required implementation artifacts:

- profile-completeness tests in `tests/test_forest_plan_profiles.py`
- if needed, helper assertions in `forest_plan_profiles.py` or test helpers only

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py`

### Sequence 1: Enrich the remaining non-Custer profiles in tracked config

Outcome label: resolved

- Author richer vocabulary and supporting-route data for the remaining non-Custer profiles using
  active local corpus evidence from the current full-canonical source set.
- Group work by compatible profile families when useful, but keep each profile’s data explicit in
  config.
- Include profile-specific district aliases, named landscapes or comparable geographic areas,
  management-area terms, overlays, and support-record trigger routes where the local corpus
  supports them.
- Record any genuinely unsupported category as an explicit accepted gap with owner and next routing
  instead of silently leaving it empty.

Required implementation artifacts:

- `config/forest_plan_profiles.json`
- if needed, small validation helpers in `forest_plan_profiles.py`

Required verification:

- `python -m json.tool config/forest_plan_profiles.json >/dev/null`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py`

### Sequence 2: Prove resolver behavior for each new profile family

Outcome label: resolved

- Add focused resolver fixtures covering selected non-Custer profiles and negative cases.
- Prove each targeted profile can:
  - resolve selected forest scope from package text
  - resolve at least one district or project-location signal
  - resolve at least one geographic area, management area, or overlay
  - route supporting FEIS/ROD/ESA evidence only when explicit package cues exist
- Prove each targeted profile still fails closed on ambiguity, generic triggers, and unselected
  profile references.

Required implementation artifacts:

- `tests/test_forest_plan_resolver.py`
- only minimal generic resolver changes needed to support new config-driven cases

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py`

### Sequence 3: Prove compliance-gate parity for expanded profiles

Outcome label: resolved

- Add compliance-review fixtures proving explicitly selected non-Custer profiles are gate-required
  and cannot pass without reviewer-ready component/adjudication evidence.
- Retain existing Custer and Beaverhead proofs while adding additional non-Custer selected-profile
  cases.
- Keep ambiguous and out-of-scope paths non-required.

Required implementation artifacts:

- `tests/test_compliance_review.py`
- only generic compliance-path changes needed for selected-profile parity

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_cli.py tests/test_architecture_contract.py`

### Sequence 4: All-R1 forest-plan verification and closeout alignment

Outcome label: resolved for the scoped profile-depth gap, reduced for the broader any-R1
real-package expansion claim

- Re-run the live all-R1 forest-plan inventory verification on the active full-canonical source
  set before closing the milestone.
- Refresh current-state docs, this milestone plan, and the session handoff with the actual
  post-closeout state and next routing.
- If the active source set or readiness contract has drifted, update the docs to the verified live
  state or stop and reroute the blocker.

Required implementation artifacts:

- refreshed status docs only if the verified live state materially changed

Required verification:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver.py tests/test_compliance_review.py tests/test_architecture_contract.py`
- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-5e65d845ce77e1a0 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
- `git diff --check`

Closeout interpretation:

- This milestone is `resolved` only for the scoped issue of missing richer profile vocabularies and
  gate parity across the tracked Region 1 forest-plan roster.
- The broader post-V1 "any R1 EA package review" problem remains `reduced` unless selected
  real-package reviews across the newly expanded profiles also pass and the strict expansion lane
  turns green.

## Required Documentation And Handoff Updates

Before milestone closeout, update as applicable:

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan file
- `docs/SESSION_HANDOFF.md`

The handoff update must record:

- the completed sequence or milestone name
- exact verification commands
- pass/fail counts
- the active source set used for all-R1 verification
- residual risks
- the next milestone boundary
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

- Every milestone-targeted non-Custer profile in `config/forest_plan_profiles.json` has explicit
  non-empty district, geographic-area, management-area, overlay, and supporting-route data, or an
  explicit accepted-gap entry is documented in this plan and routed forward.
- Resolver tests prove selected-profile scope resolution, routed supporting evidence, and
  ambiguity/out-of-scope failures for the newly enriched profile families.
- Compliance-review tests prove explicit non-Custer profile selection keeps
  `forest_plan_component_gate_reviewer_ready` strict and cannot pass without reviewer-ready
  component/adjudication support.
- The default Custer path remains compatible and green.
- The all-R1 forest-plan verification command validates all `10` tracked forest plans on the
  active full-canonical source set before closeout.
- Durable docs and the session handoff reflect the real post-closeout state and next routing.
- The milestone closes with one local atomic commit containing only the verified slice.

## Stop Conditions

- A needed profile vocabulary cannot be grounded in the active local corpus and would require
  unsupported guessing.
- Resolver or compliance broadening requires forest-specific runtime branching that cannot be
  expressed cleanly through config.
- The active source set or full-R1 inventory verification drifts in a way that reopens parser,
  extraction, or corpus-readiness work outside this milestone’s boundary.
- Required verification fails.
- Unrelated dirty work cannot be safely separated from the milestone slice.

## Local Commit Closeout Policy

- Stage only the verified milestone slice.
- Leave unrelated viewer changes, draft exports, and other dirty or untracked files alone.
- Include implementation, tests, plan updates, current-state updates, and handoff updates in the
  same local atomic commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the milestone as incomplete until that commit exists.

## Residual Risks And Next Routing

- Even after all remaining profiles gain richer tracked vocabulary, the broader post-V1 expansion
  lane may still need selected real-package proofs before strict expansion can be called ready.
- Some forests may need additional support-document curation or adjudication if corpus-backed
  vocabulary is insufficient for deterministic package review depth.
- If this milestone closes green, the next milestone should shift from profile-depth expansion to
  selected real-package proving across the expanded non-Custer roster, using the new profile data as
  the enforced baseline.
