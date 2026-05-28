# Forest Specific Example Package Boundary Milestone Plan

Date: 2026-05-24
Status: Active umbrella packet (`Milestone 0 registry and queue reroute opened locally; Milestone 1 aggregate per-forest coverage eval added locally; Milestone 2 reduced through docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md after the Lolo queue reroute and component coverage landed; Milestone 3 Lolo registry promotion and threshold ratchet are resolved locally; docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md has resolved package intake, reviewer-stack replay, Milestone 3 same-forest registry promotion, and the follow-on South Otter primary-example selection update locally; do not reopen Lolo or South Otter unless a verified gate regresses`)
Owner context: follow-on from the direct-file queue packet and the real-package review coverage lane

## Latest Local Implementation

- `config/forest_specific_example_package_registry_v1.json` now defines a
  parallel per-forest example-package contract for all `10` Region 1 forest
  units.
- The registry keeps example packages outside
  `Document_Register_Master`, maps each governed example to
  `applicable_forest_unit_ids`, names the shared contracts the agent should
  read first, and lists the per-review artifact families the agent should read
  for each available example.
- Governed example reviews currently include:
  - South Otter as the primary reviewer-ready example for
    `custer-gallatin-nf`
  - East Crazy as a supplemental reviewer-ready example for
    `custer-gallatin-nf`
  - South Plateau as the supplemental reviewer-ready expansion example for
    `custer-gallatin-nf`
  - West Reservoir as the governed `typed_blocked` example for `flathead-nf`
  - Tyler's Kitchen as the primary reviewer-ready example for `lolo-nf`
- The active Lolo follow-on has now rerouted `FOR-029` to
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`, added the
  tracked replay context plus Lolo review/component eval contracts, and made
  the Lolo forest-plan component slot load-bearing in
  `config/forest_plan_component_eval_coverage_v1.json`. Its downstream
  currentness/source-record blocker chain has since replayed the review on
  `source-set-f70ea11e04ae3d53` and made review `phase-eval` green. The
  parent packet's Milestone 3 registry and aggregate threshold ratchet is now
  implemented: `lolo-nf` routes as `real_package_examples_available`, and the
  Lolo slot is load-bearing in real-package coverage.
- The remaining `7` forests now route through
  `config/region1_forest_plan_profile_eval_coverage_v1.json` as
  `profile_eval_guidance_only` until a governed real package example exists.
- The South Otter follow-on in
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` is resolved through
  Milestone 3, and a follow-on user-directed policy update now makes South
  Otter the primary Custer Gallatin example. It promoted frozen review ID
  `region1-example-custer-gallatin-south-otter-58396` as Custer Gallatin
  registry example
  `example_id="cgnf-south-otter-forest-specific"` and coverage slot
  `coverage_slot_id="cgnf-south-otter-forest-specific"`, without changing
  distinct-forest thresholds or rerouting the source-register queue. The
  primary-selection closeout commit is `c56039b` (`Promote South Otter as
  Custer Gallatin primary`); the underlying Milestone 3 promotion closeout
  commit is `21eb2fa` (`Promote South Otter supplemental example`).
- `FOR-012` and `LEX-Q-001` now route to this packet as explicit
  `blocked` `named_blocker` queue rows because the East Crazy package is
  project-specific review guidance, not shared full-canonical master input.
- `forest-specific-example-package-eval` now provides a fail-closed aggregate
  contract over `config/forest_specific_example_package_registry_v1.json`,
  reusing the governed real-package coverage lane plus the forest-plan profile
  lane to prove explicit typed routing for every forest.
- Under this boundary, `source-register-queue-audit` should now read
  `resolution_status_counts={"blocked":9,"planned":33,"resolved":9}` with
  `blocked_current_or_project_applicable_count=9` and
  `unresolved_current_or_project_applicable_count=31`.

## Goal

Establish a governed forest-specific example-package lane that agents can
consult without contaminating the shared full-canonical master.

This packet exists to ensure:

1. project-specific example packages stay parallel to
   `Document_Register_Master`;
2. each forest gets a machine-readable routing row keyed by applicability;
3. the exact eval and artifact families an agent should read are explicit for
   each governed example; and
4. queue rows that only exist to surface a project example become explicit
   owned blockers instead of false canonical-promotion candidates.

## Non-Goals

- Do not add example-package rows to `Document_Register_Master`.
- Do not rerun source capture, package generation, or example-package review
  replays in this slice.
- Do not pretend forests without a governed real package example already have
  one.
- Do not weaken `real-package-review-coverage-eval`,
  `forest-plan-profile-eval`, or `source-register-queue-audit` to make this
  lane look more complete than it is.

## Scope

- `config/forest_specific_example_package_registry_v1.json`
- `src/usfs_r1_ea_sources/forest_specific_example_package_eval.py`
- queue-ledger routing for `FOR-012` and `LEX-Q-001`
- agent-facing routing docs:
  `docs/AGENT_START_HERE.md`, `README.md`, `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md`
- eval registry and schema docs:
  `docs/EVALUATION_COVERAGE_REGISTER.md` and `docs/OUTPUT_SCHEMAS.md`
- direct-file queue and source-truth packet docs where East Crazy can no longer
  be described as a remaining canonical promotion family
- focused contract tests for the registry, aggregate eval, and queue reroute

## Owner Surfaces

- registry:
  `config/forest_specific_example_package_registry_v1.json`
- queue routing:
  `config/source_register_queue_resolution_ledger_v1.json`
- shared coverage contracts:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`
- aggregate eval command:
  `src/usfs_r1_ea_sources/forest_specific_example_package_eval.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`
- review authorities:
  `config/replay_contexts/v1-cg-ecid-compliance-review.json`,
  `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`,
  `config/replay_contexts/west-reservoir-67436.json`
- docs:
  `docs/AGENT_START_HERE.md`,
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`
- tests:
  `tests/test_forest_specific_example_package_registry.py`,
  `tests/test_forest_specific_example_package_eval.py`,
  `tests/test_cli_eval.py`,
  `tests/test_source_register_queue_resolution.py`

## Routing Rules

- The agent must read the shared contract surfaces first, then any
  package-specific eval artifacts listed for the forest’s applicable example.
- `typed_blocked` examples are guidance only; they must not be presented as
  reviewer-ready templates.
- `profile_eval_guidance_only` forest rows must stay on the fixture/eval
  coverage contract until a governed real package example is added.
- A project-specific example package can only move into the shared master if a
  later packet proves that the row is actually shared authority-source input,
  not merely review guidance for one forest or project style.

## Weak-Point Prevention Contract

Strict field coverage: weak point forecast, owner surface, prevention gate,
fail threshold, controlled violation, future-codex misuse scenario.

### Weak Point 1

Risk: the registry starts behaving like a second master list.

Prevention:

- keep the explicit `queue_emits_load_rows=false` parallel-surface note;
- keep queue-example rows out of master-promotion outcomes in the queue ledger,
  either as unresolved named blockers while the example is unproven or as
  resolved `forest_specific_example_package` rows after a governed packet
  proves the example; and
- fail the focused tests if example routing starts pointing at master-promotion
  outcomes without a separate governed packet.

### Weak Point 2

Risk: an agent reads the wrong package for the wrong forest.

Prevention:

- require `applicable_forest_unit_ids` on every example review;
- require a single forest-routing row for every Region 1 forest; and
- require forest-routing example references to match the example review’s
  declared forest.

### Weak Point 3

Risk: missing review artifacts are hidden behind generic “example package”
language.

Prevention:

- keep artifact families explicit and per-review rather than claiming every
  package has the same lane outputs; and
- keep the shared contract surface pointing back to the real-package coverage
  and profile-eval contracts instead of silently inventing missing artifacts.

## Milestones

### Milestone 0

Open the lane:

- add the tracked per-forest registry;
- reroute `FOR-012` and `LEX-Q-001` into this packet as explicit blockers; and
- update routing docs so East Crazy stops presenting as a remaining
  full-canonical queue-promotion family.

### Milestone 1

Add the aggregate coverage gate:

- add a dedicated fail-closed aggregate eval over
  `config/forest_specific_example_package_registry_v1.json`;
- require explicit typed routing status coverage for every forest row;
- reuse the real-package review coverage lane for governed example-slot truth;
  and
- reuse the forest-plan profile eval lane for profile-only fallback truth.

### Milestone 2

Broaden governed examples:

- add new per-forest real package examples only when they have governed eval
  and package authority surfaces;
- keep existing `profile_eval_guidance_only` rows truthful until that happens;
  and
- update the registry and focused tests in the same slice.

Current Lolo follow-on:

- `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` is the first
  standalone Milestone 2 packet. It now owns the user-selected Lolo
  `Tyler's Kitchen Fuels Reduction and Forest Health Project (66344)` package,
  the related `FOR-029` queue-boundary reroute out of master-promotion
  semantics, and the tracked Lolo forest-plan component slot. The inherited
  review-scoped `phase-eval` blocker is now cleared on
  `source-set-f70ea11e04ae3d53`; the parent packet's Milestone 3 registry
  promotion and aggregate threshold ratchet is now resolved locally.

Current South Otter follow-on:

- `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` is resolved through
  Milestone 3, and the follow-on primary-example selection update makes South
  Otter the primary Custer Gallatin example. It owns the selected South Otter
  Landscape Restoration and Resilience Project (`58396`) package boundary for
  a governed Custer Gallatin example lane. Applicability, compliance review,
  V1 eval,
  forest-plan component eval/adjudication, and review `phase-eval` are green
  for `region1-example-custer-gallatin-south-otter-58396`. The registry row,
  real-package coverage slot, and component-coverage slot are now present and
  load-bearing. No queue reroute exists.

## Current Evidence

- The forest-specific registry remains the typed routing owner for every
  Region 1 forest.
- Lolo now routes as `real_package_examples_available` in
  `config/forest_specific_example_package_registry_v1.json`; that row names
  Tyler's Kitchen as the primary example and records `FOR-029` as the
  forest-specific example boundary.
- `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` is the resolved
  parent packet for the Lolo registry promotion slice.
- The source-record/currentness blocker chain is historical for Lolo; the
  current review replay passes on `source-set-f70ea11e04ae3d53`.
- `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` is the resolved
  standalone follow-on for South Otter promotion. South Otter is now the
  primary governed same-forest Custer Gallatin package-style example; East
  Crazy and South Plateau remain supplemental examples, and South Otter does
  not count as a new distinct forest.
- Current aggregate evidence after South Otter promotion:
  `real-package-review-coverage-eval` passes with `5` covered required slots,
  `4` reviewer-ready slots, `1` typed-blocked slot, `3` distinct forests, and
  `6` package-style tags. `forest-specific-example-package-eval` passes with
  `5` governed review examples, `4` reviewer-ready examples, `3` distinct
  governed forests, and `7` profile-guidance-only forests.
- `forest-plan-component-eval-coverage` still fails as an aggregate on
  pre-existing non-South Otter ECID source-delta and West Reservoir slots, but
  the South Otter component slot is required, covered, source-set aligned, and
  passing.

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Registry and queue reroute | `resolved` |
| `1` | Aggregate per-forest coverage eval | `resolved` |
| `2` | Lolo example package follow-on | `resolved` |
| `3` | Lolo registry promotion and threshold ratchet | `resolved` |
| `4` | South Otter package intake and reviewer-stack replay | `resolved` |
| `5` | South Otter registry promotion and same-forest threshold guard | `resolved` |

## Acceptance Criteria

- The registry keeps example-package routing separate from
  `Document_Register_Master`.
- Every forest row has one typed routing status and the required shared
  contract references.
- Lolo remains `real_package_examples_available` only while the parent Lolo
  registry, coverage, queue, and aggregate thresholds continue to pass
  together.
- Negative coverage remains explicit: missing or typed-blocked examples fail or
  route as guidance-only rather than silently becoming reviewer-ready.
- No tests, eval thresholds, or queue gates are weakened to make a forest appear
  covered.

## Required Verification Gates

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_specific_example_package_registry.py tests/test_forest_specific_example_package_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_real_package_review_coverage_eval.py tests/test_forest_plan_component_eval_coverage.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
git diff --check
```

## Freshness Check

Before changing registry status, read `docs/CURRENT_ROUTING.md`,
`docs/SESSION_HANDOFF.md`, `docs/CURRENT_SYSTEM_STATE.md`,
`docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
`docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`, and
`config/forest_specific_example_package_registry_v1.json`. Verify the current
Lolo and South Otter `v1-ea-eval`, review `phase-eval`, real-package coverage,
and forest-specific example-package artifacts before changing any promoted row.

## Stop Conditions

- Stop if registry promotion would require adding example-package rows to
  `Document_Register_Master`.
- Stop if a governed aggregate gate fails after registry or coverage changes.
- Stop if any forest row would become reviewer-ready without an explicit
  package authority and eval artifact family.
- Stop if the only way forward is to weaken eval thresholds, skip tests, or
  hand-edit ignored generated artifacts.

## Strict Weak-Point Prevention Contract

| Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse scenario |
| --- | --- | --- | --- | --- | --- |
| Registry behaves like a second master list | registry and source-register queue ledger | queue audit plus registry tests | project-specific example emits as shared master input | queue row stays blocked/named until proven, or resolved as `forest_specific_example_package` after a governed packet proves the parallel example | a future session silently promotes example rows into the master workbook lane |
| Forest row points at the wrong example | registry example rows | forest-specific example eval | example forest IDs and registry applicability IDs disagree | typed-blocked/profile-only rows remain guidance-only | a future session reuses a Custer example as Lolo guidance without applicability proof |
| Missing artifacts are hidden by generic wording | real-package coverage and profile-eval contracts | aggregate eval plus negative coverage cases | missing required review artifact is counted reviewer-ready | typed-blocked and profile-only states fail closed | a future session presents profile-only fixtures as a governed real package |
| Lolo is promoted before threshold ratchet | Lolo parent packet and registry config | Milestone 3 aggregate gate bundle | `lolo-nf` status changes without coverage/queue threshold updates | keep Lolo promoted only while the ratcheted gates pass | a future session changes only the registry label after phase-eval turns green |

## Local Commit Closeout Policy

`complete-after-commit` rule: a milestone is not complete until verification
passes, durable docs and handoff updates land, and the local atomic commit
exists. Stage only the verified slice for the current milestone. Leave ignored
`source_library/` evidence unstaged unless repository policy changes.
