# Oversized Test Owner Boundary Milestone Plan

Date: 2026-05-26

Status: queued standalone architecture child packet opened 2026-05-26 for the five live
oversized test owners and the adjacent concentrated test-hotspot guard; no implementation
milestones are closed yet

Owner context: this packet stacks under the now-resolved
`docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md`. It is not the current live
architecture next step. `docs/CURRENT_SYSTEM_STATE.md` now routes the reopened oversized backlog in
two stages: the four source owners first, then the five test owners. This plan therefore queues the
test half of that backlog behind the source-owner follow-ons already routed from
`config/architecture_large_file_inventory_v1.json`.

This packet also must preserve one historical truth rather than reopening it:
`docs/COMPLIANCE_REVIEW_TEST_BOUNDARY_MILESTONE_PLAN.md` already closed the broad
`tests/test_compliance_review.py` catch-all split. The current `tests/test_compliance_review.py`
still matters because the fresh architecture probe ranks it as the top churn hotspot, but this
packet should keep that suite behind its existing boundary gate rather than treating it as another
oversized file.

## Purpose

Resolve the current oversized-test backlog and make the remaining churn-only hotspot debt explicit
and fail-closed.

The exact weakness is not only that five test files are above `800` lines. The deeper problem is
that these files still mix multiple owner responsibilities and local helper families, which keeps
review cost high and encourages future sessions to add the next case to the wrong file.

This packet exists to:

- reduce every live oversized test owner below the `800`-line architecture gate;
- split mixed-owner test behavior into owner-aligned suites and shared support modules; and
- keep `tests/test_compliance_review.py` from regrowing while the remaining test backlog is paid
  down.

## Current Evidence

### Live oversized test backlog on 2026-05-26

- `docs/CURRENT_SYSTEM_STATE.md` now records the resolved architecture-control-plane state and the
  live reopened backlog at `9` code files above `800`, split into `4` source owners and `5` test
  owners.
- The current oversized test owners are:
  - `tests/test_applicability_authority_family_templates.py` at `1407` lines
  - `tests/test_promotion_suite_full_canonical.py` at `913` lines
  - `tests/test_extraction_accuracy.py` at `847` lines
  - `tests/test_forest_plan_resolver_scope.py` at `829` lines
  - `tests/test_catalog.py` at `820` lines
- `config/architecture_large_file_inventory_v1.json` already routes those five owners explicitly as:
  - `test-applicability-authority-family-templates-owner`
  - `test-promotion-suite-full-canonical-owner`
  - `test-extraction-accuracy-owner`
  - `test-forest-plan-resolver-scope-owner`
  - `test-catalog-owner`

### Natural split seams already visible in the files

- `tests/test_applicability_authority_family_templates.py` has one class but clearly separates:
  - core candidate-contract behavior near the top of the file; and
  - repeated current-source replacement and family-specific reconciliation cases across the back
    half of the file.
- `tests/test_catalog.py` mixes:
  - canonical catalog artifact/SQLite contract checks;
  - legacy single-run and batch-run linking behavior;
  - forest-plan and source-delta role classification; and
  - local artifact writer helpers at the bottom of the file.
- `tests/test_extraction_accuracy.py` mixes:
  - direct audit metric behavior;
  - direct-parse versus reuse-admission contract cases;
  - parser-route and direct-file parser acceptance cases; and
  - local payload/download helpers at the bottom of the file.
- `tests/test_forest_plan_resolver_scope.py` mixes:
  - profile location resolution;
  - supporting-route trigger behavior;
  - readiness and reviewer-resolution cases; and
  - all of that sits in one file even though shared forest-plan resolver support already exists in
    `tests/support/forest_plan_resolver_common.py` and
    `tests/support/forest_plan_resolver_custer_fixtures.py`.
- `tests/test_promotion_suite_full_canonical.py` mixes:
  - the committed full-canonical manifest contract; and
  - runtime suite result behavior and path-resolution cases;
  - while an existing support owner already exists at `tests/support/promotion_suite_fixtures.py`.

### Adjacent churn hotspot that must stay guarded

- The fresh architecture probe captured in
  `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md` still reports
  `tests/test_compliance_review.py` as the repo's top hotspot by churn/size even though it is now
  `644` lines and no longer part of the oversized-file inventory.
- `docs/COMPLIANCE_REVIEW_TEST_BOUNDARY_MILESTONE_PLAN.md` is historical closeout for that earlier
  split. This packet should reuse its guardrail pattern, not reopen its production or suite routing.

## Goal

Resolve the scoped test-owner debt by turning each current oversized test owner into a bounded core
suite plus explicit sibling owners or support modules, while preserving existing behavior and
architecture gates.

Completion means all of the following are true:

- the five currently oversized test owners are all below `800` lines;
- no newly created test or `tests/support/` helper file introduced by this packet exceeds `800`
  lines;
- each split follows a named owner boundary instead of one large miscellaneous test file;
- the architecture inventory, architecture-quality gate, and current-state docs are updated in the
  same milestone commits that lower the live oversized count; and
- `tests/test_compliance_review.py` remains behind its existing boundary gate so the repo does not
  solve five oversized tests while regrowing the already-split compliance hotspot.

## Non-Goals

- Do not reopen the production source-owner splits that belong to the four source backlog files.
- Do not reopen `docs/COMPLIANCE_REVIEW_TEST_BOUNDARY_MILESTONE_PLAN.md` or move compliance
  behaviors back into `tests/test_compliance_review.py`.
- Do not weaken tests, delete negative cases, add skips/xfails, or replace focused coverage with
  broader but looser smoke tests.
- Do not introduce a new catch-all support file that simply replaces one oversized test with one
  oversized fixture module.
- Do not stage ignored `source_library/` outputs.

## Scope

In scope:

- the five current oversized test owners
- new owner-aligned sibling suites under `tests/`
- new or extended shared helpers under `tests/support/`
- architecture inventory and gate updates that must move with the count change
- docs and handoff updates required to route the reduced backlog truthfully
- no-regrowth verification for the existing compliance test hotspot boundary

Out of scope:

- production code refactors except for narrow import or fixture alignment when a test split requires
  it
- new evaluator behavior or new corpus captures
- a second pass on the source-owner backlog files
- broad cleanup of unrelated smaller tests

## Owner Surfaces

| Surface | Required role after closeout | Required verification |
| --- | --- | --- |
| `tests/test_applicability_authority_family_templates.py` | narrow core owner for template-candidate contract behavior | focused pytest, boundary gate |
| sibling applicability template suites and support | own family-specific current-source reconciliation and shared fixture builders | focused pytest, boundary gate |
| `tests/test_catalog.py` | narrow core owner for canonical catalog engine-artifact and SQLite behavior | focused pytest, boundary gate |
| sibling catalog suites and support | own legacy run linking, batch linking, and source-delta/forest-plan classification helpers | focused pytest, boundary gate |
| `tests/test_extraction_accuracy.py` | narrow core owner for audit behavior and contract-level summary checks | focused pytest, boundary gate |
| sibling extraction-accuracy suites and support | own direct-parse/reuse-admission scenarios, parser-route scenarios, and helper writers | focused pytest, boundary gate |
| `tests/test_forest_plan_resolver_scope.py` | narrow core owner for primary scope-resolution behavior | focused pytest, boundary gate |
| sibling forest-plan resolver scope suites and support | own supporting-route, readiness, and reviewer-resolution behavior | focused pytest, boundary gate |
| `tests/test_promotion_suite_full_canonical.py` | narrow core owner for committed full-canonical contract behavior | focused pytest, boundary gate |
| sibling promotion full-canonical suites and support | own runtime suite results and artifact-path behavior | focused pytest, boundary gate |
| `tests/test_oversized_test_owner_boundaries.py` or equivalent per-owner boundary tests | fail closed on line-budget drift, forbidden imports, and helper leakage across the five owners | focused pytest |
| `tests/test_compliance_review_test_boundary.py` | keep the earlier compliance hotspot split from regrowing while this packet changes other large tests | focused pytest |
| `config/architecture_large_file_inventory_v1.json` | current live oversized-file source of truth as the count decreases | focused pytest readback |
| `tests/test_architecture_quality.py` | exact live oversized-file and route/doc gate | focused pytest, ruff, compileall |
| `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and this plan | truthful current routing for the shrinking test backlog | targeted grep, `git diff --check` |

## Placement Rules

- Keep the current root test paths as narrow core owners where that makes routing easier:
  - `tests/test_applicability_authority_family_templates.py`
  - `tests/test_catalog.py`
  - `tests/test_extraction_accuracy.py`
  - `tests/test_forest_plan_resolver_scope.py`
  - `tests/test_promotion_suite_full_canonical.py`
- Move satellite behaviors into sibling suites named for the owner they verify. Suggested patterns:
  - `tests/test_applicability_authority_family_templates_current_sources.py`
  - `tests/test_catalog_legacy_linking.py`
  - `tests/test_extraction_accuracy_admission_contracts.py`
  - `tests/test_forest_plan_resolver_scope_supporting_routes.py`
  - `tests/test_promotion_suite_full_canonical_runtime.py`
- Move large builder helpers into explicit `tests/support/` owners named for the lane. Do not create
  a generic `tests/support/test_utils.py`.
- If a new support owner grows above `600` lines during implementation, split it again in the same
  milestone instead of accepting a near-replacement hotspot.
- Keep `tests/test_compliance_review.py` and `tests/test_compliance_review_test_boundary.py` as the
  existing pattern for a narrowed core suite plus explicit boundary guard. This packet should reuse
  that pattern rather than reworking the compliance lane.
- Each milestone that reduces the oversized backlog must update
  `config/architecture_large_file_inventory_v1.json`, `tests/test_architecture_quality.py`,
  `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md` in the same commit so the gate
  remains exact.

## Weak-Point Prevention Contract

| Milestone | Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse prevented |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | The packet starts from stale queue order and claims the test lane is next even though source-owner backlog is still ahead | this plan, current-state docs, inventory | architecture probe readback, current-state readback, focused baseline tests | the packet is treated as the active next architecture slice while source-owner backlog still routes first | pre-edit baseline must still show source owners first and five test owners second in current-state docs | a future session implements the wrong backlog half because the new test packet sounded more convenient |
| `1` | A test file is split by line range only, but ownership stays mixed and failures remain hard to localize | new owner suites, boundary gate | focused pytest plus boundary test on imports/helper locations | the retained root file still imports or defines behaviors that belong to sibling owners | re-add a forbidden helper or import to a narrowed root suite; the boundary test must fail | a future session puts one more family-specific case back into the core file because it is nearby |
| `2` | Local helper extraction just moves the hotspot into one oversized `tests/support/` file | new support owners | line-budget check in boundary gate plus `wc -l` | any new support file created by this packet exceeds `800` lines, or exceeds `600` without same-milestone resplit | deliberately overfill a fixture owner past the budget in a controlled boundary fixture; the gate must fail | a future session replaces one big test with one bigger helper and calls the debt resolved |
| `3` | The architecture gate is weakened to accept the new split instead of staying exact | inventory, `tests/test_architecture_quality.py` | focused pytest, inventory readback, probe rerun | count or path assertions become looser than the exact live backlog after a milestone | remove one reduced file from the inventory or allow a stale count; the gate must fail | a future session drops the exact count to get green faster |
| `4` | The existing compliance hotspot regrows while other oversized tests are being reduced | `tests/test_compliance_review.py`, `tests/test_compliance_review_test_boundary.py` | focused pytest on the compliance boundary gate | the compliance suite regrows mixed-owner imports or exceeds its locked boundary budget | re-add a forbidden non-core compliance import; the compliance boundary test must fail | a future session pays down five tests but quietly recreates the already-closed compliance hotspot |

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Freshness and queue-order lock | `resolved` |
| `1` | Applicability authority-family template test owner split | `resolved` |
| `2` | Catalog test owner split | `resolved` |
| `3` | Extraction-accuracy test owner split | `resolved` |
| `4` | Forest-plan resolver scope test owner split | `resolved` |
| `5` | Promotion-suite full-canonical test owner split | `resolved` |
| `6` | Cross-suite hotspot lock, inventory closeout, and docs alignment | `resolved` |

### Milestone `0`: Freshness and queue-order lock

Outcome label: `resolved`

Work:

- Reproduce the live oversized test set, current line counts, and current test-hotspot note before
  any edits.
- Confirm from current-state docs that this packet is queued behind the source-owner backlog rather
  than replacing the active replay or source-owner architecture routes.
- Design the boundary gate first:
  - one central `tests/test_oversized_test_owner_boundaries.py`, or
  - one equivalent per-owner boundary suite,
  provided the gate itself stays small and explicit.

Required verification:

```bash
git status -sb
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
wc -l tests/test_applicability_authority_family_templates.py tests/test_catalog.py tests/test_promotion_suite_full_canonical.py tests/test_extraction_accuracy.py tests/test_forest_plan_resolver_scope.py tests/test_compliance_review.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py tests/test_compliance_review_test_boundary.py -q
rg -n "five test owners|top hotspot|tests/test_compliance_review.py|test-applicability-authority-family-templates-owner|test-catalog-owner" docs/CURRENT_SYSTEM_STATE.md docs/SESSION_HANDOFF.md config/architecture_large_file_inventory_v1.json docs/COMPLIANCE_REVIEW_TEST_BOUNDARY_MILESTONE_PLAN.md
git diff --check
```

### Milestone `1`: Applicability authority-family template test owner split

Outcome label: `resolved`

Work:

- Keep `tests/test_applicability_authority_family_templates.py` as the narrow core owner for
  template-candidate contract behavior.
- Move current-source replacement and family-specific reconciliation cases into sibling owner suites.
- Move repeated template-set and catalog-row builders into a named `tests/support/` fixture owner if
  needed.
- Update the inventory, exact oversized-file count gate, and current-state docs in the same
  milestone commit.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_authority_family_templates*.py tests/test_authority_family_rule_templates.py tests/test_authority_universe_inventory.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_applicability_authority_family_templates*.py tests/test_authority_family_rule_templates.py tests/test_authority_universe_inventory.py tests/test_architecture_quality.py
PYTHONPATH=src python -m compileall tests
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `2`: Catalog test owner split

Outcome label: `resolved`

Work:

- Keep `tests/test_catalog.py` as the narrow core owner for canonical catalog engine-artifact and
  SQLite behavior.
- Move legacy run linking, batch linking, and source-delta/forest-plan role classification into
  sibling owner suites.
- Move download-run and batch-manifest writers into a named catalog support owner.
- Update the inventory, exact oversized-file count gate, and current-state docs in the same
  milestone commit.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog*.py tests/test_source_register_loader.py tests/test_source_register_schema.py tests/test_dry_run.py tests/test_preflight.py tests/test_cli.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_catalog*.py tests/test_source_register_loader.py tests/test_source_register_schema.py tests/test_dry_run.py tests/test_preflight.py tests/test_cli.py tests/test_architecture_quality.py
PYTHONPATH=src python -m compileall tests
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `3`: Extraction-accuracy test owner split

Outcome label: `resolved`

Work:

- Keep `tests/test_extraction_accuracy.py` as the narrow core owner for audit behavior and
  contract-level summary checks.
- Move direct-parse/reuse-admission cases, parser-route acceptance cases, and helper writers into
  sibling owners or named support modules.
- Reuse the lane's existing extraction-fidelity and extraction-admission contracts; do not convert
  the split into a behavior redesign.
- Update the inventory, exact oversized-file count gate, and current-state docs in the same
  milestone commit.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_extraction_accuracy*.py tests/test_extraction_admission.py tests/test_authority_currentness.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_extraction_accuracy*.py tests/test_extraction_admission.py tests/test_authority_currentness.py tests/test_architecture_quality.py
PYTHONPATH=src python -m compileall tests
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `4`: Forest-plan resolver scope test owner split

Outcome label: `resolved`

Work:

- Keep `tests/test_forest_plan_resolver_scope.py` as the narrow core owner for primary
  scope-resolution behavior.
- Move supporting-route triggers, readiness gates, and reviewer-resolution behavior into sibling
  owner suites as needed.
- Reuse the existing `tests/support/forest_plan_resolver_common.py` and
  `tests/support/forest_plan_resolver_custer_fixtures.py` support owners where possible before
  creating new ones.
- Update the inventory, exact oversized-file count gate, and current-state docs in the same
  milestone commit.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver_scope*.py tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_forest_plan_resolver_scope*.py tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py tests/test_architecture_quality.py
PYTHONPATH=src python -m compileall tests
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `5`: Promotion-suite full-canonical test owner split

Outcome label: `resolved`

Work:

- Keep `tests/test_promotion_suite_full_canonical.py` as the narrow core owner for the committed
  full-canonical manifest contract.
- Move runtime suite-result and artifact-path behavior into sibling owner suites.
- Reuse or extend `tests/support/promotion_suite_fixtures.py` rather than creating duplicate
  promotion fixture builders.
- Update the inventory, exact oversized-file count gate, and current-state docs in the same
  milestone commit.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite_full_canonical*.py tests/test_promotion_suite.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_promotion_suite_full_canonical*.py tests/test_promotion_suite.py tests/test_architecture_quality.py
PYTHONPATH=src python -m compileall tests
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

### Milestone `6`: Cross-suite hotspot lock, inventory closeout, and docs alignment

Outcome label: `resolved`

Work:

- Finish the cross-suite boundary gate so it fails closed on:
  - regrown line budgets
  - forbidden owner imports
  - helper leakage back into the root core suites
  - oversize support-file substitutions
- Re-run `tests/test_compliance_review_test_boundary.py` and keep the compliance core suite behind
  its existing boundary.
- Update `config/architecture_large_file_inventory_v1.json`,
  `tests/test_architecture_quality.py`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/SESSION_HANDOFF.md` so the reduced test backlog and any remaining non-test source backlog
  are routed truthfully.
- If the fresh architecture probe still ranks `tests/test_compliance_review.py` as the top hotspot
  by churn after these splits, record that as an explicit, already-guarded residual rather than
  pretending the oversized-test packet still failed.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_oversized_test_owner_boundaries.py tests/test_compliance_review_test_boundary.py tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_authority_family_templates*.py tests/test_catalog*.py tests/test_extraction_accuracy*.py tests/test_forest_plan_resolver_scope*.py tests/test_promotion_suite_full_canonical*.py -q
PYTHONPATH=src uv run --extra dev ruff check tests
PYTHONPATH=src python -m compileall tests
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

## Required Implementation Artifacts

- narrowed root owners for the five current oversized test files
- new owner-aligned sibling suites under `tests/`
- new or extended named fixture/support owners under `tests/support/`
- a boundary gate for the five oversized test owners
- updated `config/architecture_large_file_inventory_v1.json`
- updated `tests/test_architecture_quality.py`

## Required Documentation And Handoff Updates

- `config/architecture_large_file_inventory_v1.json`
- `tests/test_architecture_quality.py`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this packet with milestone status updates if execution starts here
- `docs/TECH_DEBT_REGISTER.md` only if an explicitly approved temporary shortcut is introduced

## Required Verification Gates

- Exact architecture gate:
  - `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
- Focused boundary guards:
  - `PYTHONPATH=src uv run --extra dev pytest tests/test_oversized_test_owner_boundaries.py tests/test_compliance_review_test_boundary.py -q`
- Focused split-suite verification for the touched owner family in each milestone
- Static quality:
  - `PYTHONPATH=src uv run --extra dev ruff check tests`
  - `PYTHONPATH=src python -m compileall tests`
  - `git diff --check`
- Fresh hotspot/large-file readback:
  - `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20`

## Acceptance Criteria

- All five currently oversized test owners are below `800` lines.
- No new test or `tests/support/` file created by this packet exceeds `800` lines.
- The narrowed root suites no longer directly own the satellite behaviors or large helper families
  moved into sibling suites/support owners.
- `config/architecture_large_file_inventory_v1.json` and `tests/test_architecture_quality.py`
  match the exact reduced live oversized-file set after each milestone closeout.
- `tests/test_compliance_review_test_boundary.py` stays green and `tests/test_compliance_review.py`
  does not regrow mixed-owner imports or line-budget drift during this packet.
- If the fresh architecture probe still lists `tests/test_compliance_review.py` as the top hotspot,
  the docs route it explicitly as a guarded residual rather than silently treating it as unresolved
  oversized backlog.
- No same-milestone test split relies on weaker assertions, skipped coverage, or undocumented
  temporary debt.

## Stop Conditions

- Stop if a split would require production-behavior changes rather than test-owner separation.
- Stop if the source-owner architecture backlog is still the chosen live next slice and this packet
  would displace it without an explicit user reprioritization.
- Stop if the only path to green is looser assertions, new skips/xfails, or oversized support-file
  substitution.
- Stop if the architecture inventory or quality gate cannot stay exact during a count reduction.

## Local Commit Closeout Policy

- Complete one milestone at a time.
- Each milestone must land as one local atomic commit containing:
  - the narrowed test owner(s)
  - any new sibling suites or support owners
  - matching boundary-gate updates
  - inventory/gate updates
  - current-state and handoff updates
- Do not stage unrelated dirty worktree changes or ignored `source_library/` outputs.

## Residual Risks And Next Milestone Routing

- This packet is queued behind the four source-owner architecture follow-ons recorded in
  `docs/CURRENT_SYSTEM_STATE.md`. If those source-owner packets remain open, this packet stays
  queued.
- If the five oversized test owners close but a churn-only hotspot remains in
  `tests/test_compliance_review.py`, route that residual through the already-closed compliance
  boundary pattern and current architecture docs instead of reopening the oversized-test packet.
- If new large-file debt appears elsewhere during implementation, rerun the architecture probe and
  update the live queue before continuing.
