# Forest Specific Example Package Boundary Milestone Plan

Date: 2026-05-24
Status: Active umbrella packet (`Milestone 0 registry and queue reroute opened locally; Milestone 1 aggregate per-forest coverage eval added locally; Milestone 2 reduced through docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md after the Lolo queue reroute and component coverage landed; Milestone 3 Lolo registry promotion and threshold ratchet are resolved locally; docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md has resolved package intake, reviewer-stack replay, Milestone 3 same-forest registry promotion, and the follow-on South Otter primary-example selection update locally; docs/HLC_BONANZA_EXAMPLE_PACKAGE_MILESTONE_PLAN.md is resolved through Milestone 4 registry and coverage promotion; docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md is resolved through Milestone 2 after f70 source-record, component-inventory, and component-adjudication closure without registry promotion; South Plateau is archived as historical evidence only and must not be used as an example; do not reopen Lolo, South Otter, HLC, or Bitterroot Milestones 0-2 unless a verified gate regresses`)
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
  - West Reservoir as the primary reviewer-ready example for `flathead-nf`
  - Tyler's Kitchen as the primary reviewer-ready example for `lolo-nf`
  - Bonanza as the primary reviewer-ready example for `helena-lewis-and-clark-nf`
- South Plateau is no longer an active governed example. It is retained only
  under archived manifest surfaces with
  `usage_policy="historical_evidence_only_not_example"` due to litigation and
  Forest Plan compliance challenge risk.
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
- The remaining `6` forests now route through
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
- The HLC Bonanza follow-on in
  `docs/HLC_BONANZA_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` is resolved through
  Milestone 4. Local package authority, package cache, HLC component
  adjudication, area evidence, applicability replay, generated rule pack,
  compliance review, V1 eval, component eval, review `phase-eval`, real-package
  coverage, and forest-specific registry eval now pass. HLC routes as
  `real_package_examples_available` with Bonanza as the primary example.
- The Bitterroot Front follow-on in
  `docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` is resolved through
  Milestone 2 forest-plan resolver preflight. `FOR-007` now routes to that
  packet as planned `forest_specific_example_package` queue-boundary work,
  local package authority and the base `ea-review` cache are green, and
  Bitterroot scope resolves to `bitterroot_nf`. The local f70 source-record
  overlay now indexes `R1PLAN-bitterroot-nf-12`/`-13`, the f70 review-local
  component inventory now passes with `23` components and `3` standards from
  `FOR-005`/`FOR-006`, and tracked component adjudication passes with `20/20`
  items resolved. Raw applicable-standard coverage remains red as Milestone 3
  reviewer-stack/component-eval diagnostic evidence. `bitterroot-nf` stays
  `profile_eval_guidance_only` until reviewer-stack and promotion gates pass.
- `FOR-012` and `LEX-Q-001` now route to this packet as explicit
  `blocked` `named_blocker` queue rows because the East Crazy package is
  project-specific review guidance, not shared full-canonical master input.
- `forest-specific-example-package-eval` now provides a fail-closed aggregate
  contract over `config/forest_specific_example_package_registry_v1.json`,
  reusing the governed real-package coverage lane plus the forest-plan profile
  lane to prove explicit typed routing for every forest.
- Under this boundary, `source-register-queue-audit` should now read
  `planned_disposition_counts={"forest_specific_example_package":2,"promote_direct_file":34}`
  and `resolution_status_counts={"blocked":9,"planned":33,"resolved":9}` with
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
- governed review authorities:
  `config/replay_contexts/v1-cg-ecid-compliance-review.json`,
  `config/replay_contexts/west-reservoir-67436.json`,
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/replay_contexts/region1-example-custer-gallatin-south-otter-58396.json`,
  `config/replay_contexts/region1-example-helena-lewis-and-clark-bonanza-66532.json`
- archived review authority:
  `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`
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

Current HLC Bonanza follow-on:

- `docs/HLC_BONANZA_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` is resolved through
  Milestone 4 and is the system-facing HLC example-package owner. For
  `helena-lewis-and-clark-nf`, the registry must keep
  `primary_example_id="hlc-bonanza-forest-specific"` and agents must inspect
  Bonanza first for HLC example-package guidance. The package is not generic
  Region 1 guidance, is not reusable for other forests, and remains parallel to
  `Document_Register_Master`.

Current Bitterroot Front follow-on:

- `docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` is active after a
  resolved Milestone 2 forest-plan resolver preflight. It owns the user-selected
  Bitterroot Front Project (`57341`) package boundary for a governed Bitterroot
  candidate lane. `FOR-007` is packet-owned as a planned forest-specific
  example boundary, but Bitterroot remains profile-guidance-only until the
  reviewer-stack, component-eval, and registry promotion gates pass. The
  planned identity is
  `review_id="region1-example-bitterroot-front-57341"` and
  `example_id="bitterroot-front-forest-specific"`.

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
  Crazy remains the only supplemental active example, South Plateau is
  archived as historical evidence only, and South Otter does not count as a
  new distinct forest.
- Current aggregate evidence after HLC Bonanza promotion:
  `real-package-review-coverage-eval` passes with `5` covered required slots,
  `5` reviewer-ready slots, `0` typed-blocked slots, `4` distinct forests, and
  `6` package-style tags. `forest-specific-example-package-eval` passes with
  `5` governed review examples, `5` reviewer-ready examples, `4` distinct
  governed forests, and `6` profile-guidance-only forests.
- Bitterroot Front package-authority evidence is local and ignored:
  `source_library/reviews/_intake/region1-example-bitterroot-front-57341/`
  contains `box_inventory.json` with `41` folders, `132` visible files, and
  `632,912,037` expected bytes, plus `box_import_manifest.json` with `132`
  downloaded files, `632,912,037` actual bytes, and `failure_count=0`.
  `config/replay_contexts/region1-example-bitterroot-front-57341.json` now
  points at `source-set-f70ea11e04ae3d53` and the repo-root current catalog.
  Base `ea-review` passes with `132/132` files extracted, `5,463` package
  chunks, `package_failed_count=0`, `validation_passed=true`, and
  `reviewer_ready=true`. Forest-plan resolver preflight now resolves
  `scope_status="bitterroot_nf"` with `1` project-location signal,
  `4` management areas, `2` overlays, and `0` unresolved mentions, and context
  validation passes after the local f70 source-record overlay indexed
  `R1PLAN-bitterroot-nf-12` and `R1PLAN-bitterroot-nf-13` with `115` and `136`
  chunks. The local f70 catalog/retrieval overlay has `717` source rows, `705`
  artifacts, and `9` supplemental overlay rows. The review-local f70
  manifest-driven component inventory now emits `23` components and `3`
  standards from `FOR-005`/`FOR-006` with `coverage_passed=true`. Tracked
  component adjudication now passes with `20/20` items resolved, `0` pending,
  `12` applicability false positives, and `8` evidence-linking misses; rerun
  resolver validation is green with `needs_reviewer_resolution=false`. Raw
  applicable-standard coverage remains red with `3` applicable standards and
  `1` applied standard as Milestone 3 diagnostic evidence. `FOR-007` is no
  longer a generic direct-file promotion candidate, but there is still no
  Bitterroot reviewer-ready example row, real-package coverage slot,
  component-coverage slot, V1 eval contract, compliance review, passing
  component eval, or review `phase-eval` promotion proof.
- `forest-plan-component-eval-coverage` still fails as an aggregate on the
  pre-existing ECID source-delta slot, but the Lolo, South Otter, West
  Reservoir, and HLC Bonanza component slots are required, covered, source-set
  aligned, and passing.

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Registry and queue reroute | `resolved` |
| `1` | Aggregate per-forest coverage eval | `resolved` |
| `2` | Lolo example package follow-on | `resolved` |
| `3` | Lolo registry promotion and threshold ratchet | `resolved` |
| `4` | South Otter package intake and reviewer-stack replay | `resolved` |
| `5` | South Otter registry promotion and same-forest threshold guard | `resolved` |
| `6` | HLC Bonanza package intake through registry and coverage promotion | `resolved` |
| `7` | Bitterroot Front packet opening and FOR-007 queue boundary | `resolved` |
| `8` | Bitterroot Front package authority intake and base EA review cache | `resolved` |
| `9` | Bitterroot Front forest-plan resolver preflight with f70 source-record, component-inventory, and component-adjudication closure | `resolved` |

## Acceptance Criteria

- The registry keeps example-package routing separate from
  `Document_Register_Master`.
- Every forest row has one typed routing status and the required shared
  contract references.
- Lolo remains `real_package_examples_available` only while the parent Lolo
  registry, coverage, queue, and aggregate thresholds continue to pass
  together.
- HLC remains `real_package_examples_available` only while Bonanza's
  package-authority, V1 eval, component-eval, review-scope promotion, and
  registry/coverage slots remain aligned.
- Bitterroot remains `profile_eval_guidance_only` until Bitterroot Front
  package authority, reviewer-stack gates, and registry/coverage promotion pass.
- Negative coverage remains explicit: missing or typed-blocked examples fail or
  route as guidance-only rather than silently becoming reviewer-ready.
- No tests, eval thresholds, or queue gates are weakened to make a forest appear
  covered.

## Required Verification Gates

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_specific_example_package_registry.py tests/test_forest_specific_example_package_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_real_package_review_coverage_eval.py tests/test_forest_plan_component_eval_coverage.py
PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_queue_resolution.py
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
git diff --check
```

The standalone `forest-plan-component-eval-coverage` command is still expected
to fail until the separate ECID source-delta component-coverage blocker is
repaired. For HLC, the required check is that the Bonanza slot is present,
covered, source-set aligned, and passing, and that review `phase-eval` consumes
that review-scope summary successfully.

## Freshness Check

Before changing registry status, read `docs/CURRENT_ROUTING.md`,
`docs/SESSION_HANDOFF.md`, `docs/CURRENT_SYSTEM_STATE.md`,
`docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
`docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`, and
`docs/HLC_BONANZA_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
`docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`, and
`config/forest_specific_example_package_registry_v1.json`. Verify the current
Lolo, South Otter, and HLC Bonanza `v1-ea-eval`, review `phase-eval`,
real-package coverage, and forest-specific example-package artifacts before
changing any promoted row. For Bitterroot, verify that only Milestones 0-2
boundary/package-authority/source-record/component-inventory routing exists
until component adjudication, applicable-standard coverage, reviewer-stack,
and promotion gates pass.

## Stop Conditions

- Stop if registry promotion would require adding example-package rows to
  `Document_Register_Master`.
- Stop if a promoted forest's own registry, coverage, or review-scope gate
  fails after registry or coverage changes.
- Stop if any forest row would become reviewer-ready without an explicit
  package authority and eval artifact family.
- Stop if the only way forward is to weaken eval thresholds, skip tests, or
  hand-edit ignored generated artifacts.

## Strict Weak-Point Prevention Contract

| Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse scenario |
| --- | --- | --- | --- | --- | --- |
| Registry behaves like a second master list | registry and source-register queue ledger | queue audit plus registry tests | project-specific example emits as shared master input | queue row stays blocked/named until proven, or resolved as `forest_specific_example_package` after a governed packet proves the parallel example | a future session silently promotes example rows into the master workbook lane |
| Forest row points at the wrong example | registry example rows | forest-specific example eval | example forest IDs and registry applicability IDs disagree | typed-blocked/profile-only rows remain guidance-only | a future session reuses Custer, Lolo, Flathead, HLC, or Bitterroot package guidance for another forest without applicability proof |
| Missing artifacts are hidden by generic wording | real-package coverage and profile-eval contracts | aggregate eval plus negative coverage cases | missing required review artifact is counted reviewer-ready | typed-blocked and profile-only states fail closed | a future session presents profile-only fixtures as a governed real package |
| Lolo is promoted before threshold ratchet | Lolo parent packet and registry config | Milestone 3 aggregate gate bundle | `lolo-nf` status changes without coverage/queue threshold updates | keep Lolo promoted only while the ratcheted gates pass | a future session changes only the registry label after phase-eval turns green |

## Local Commit Closeout Policy

`complete-after-commit` rule: a milestone is not complete until verification
passes, durable docs and handoff updates land, and the local atomic commit
exists. Stage only the verified slice for the current milestone. Leave ignored
`source_library/` evidence unstaged unless repository policy changes.
