# Forest Specific Example Package Boundary Milestone Plan

Date: 2026-05-23
Status: Active packet (`Milestone 0 registry and queue reroute opened locally; Milestone 1 aggregate per-forest coverage eval added locally; Milestone 2 next when additional governed per-forest example packages are added`)
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
  - East Crazy as the primary reviewer-ready example for
    `custer-gallatin-nf`
  - South Plateau as the supplemental reviewer-ready expansion example for
    `custer-gallatin-nf`
  - West Reservoir as the governed `typed_blocked` example for `flathead-nf`
- The remaining `8` forests now route through
  `config/region1_forest_plan_profile_eval_coverage_v1.json` as
  `profile_eval_guidance_only` until a governed real package example exists.
- `FOR-012` and `LEX-Q-001` now route to this packet as explicit
  `blocked` `named_blocker` queue rows because the East Crazy package is
  project-specific review guidance, not shared full-canonical master input.
- `forest-specific-example-package-eval` now provides a fail-closed aggregate
  contract over `config/forest_specific_example_package_registry_v1.json`,
  reusing the governed real-package coverage lane plus the forest-plan profile
  lane to prove explicit typed routing for every forest.
- Under this boundary, `source-register-queue-audit` should now read
  `resolution_status_counts={"blocked":9,"planned":34,"resolved":8}` with
  `blocked_current_or_project_applicable_count=9` and
  `unresolved_current_or_project_applicable_count=32`.

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

### Weak Point 1

Risk: the registry starts behaving like a second master list.

Prevention:

- keep the explicit `queue_emits_load_rows=false` parallel-surface note;
- keep queue-example rows blocked in the queue ledger instead of silently
  resolved; and
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
