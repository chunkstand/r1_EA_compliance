# Idaho Panhandle Lacy Lemoosh Example Package Milestone Plan

Date: 2026-05-29
Status: Active. Milestone 0 is resolved locally; Milestone 1 package-authority
intake is the next implementation slice.
Plan class: implementation
High-risk implementation: yes
Owner context: standalone follow-on from `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Commit policy: each completed milestone closes only after verification,
affected docs/handoff updates, and a local atomic commit.

## Purpose

Open the governed Idaho Panhandle National Forests example-package lane around
the user-selected Lacy Lemoosh EA package without contaminating
`Document_Register_Master` or claiming reviewer-ready status before
deterministic review gates pass.

Selected package authority:

- project page: `https://www.fs.usda.gov/r01/idahopanhandle/projects/60853`
- project title and ID: `Lacy Lemoosh`, `60853`
- public Pinyon/Box folder:
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158229569265`
- Box root label: `Lacy Lemoosh (60853)`
- forest and district: `idaho-panhandle-nfs`, `St. Maries Ranger District`
- expected analysis type/status: `Environmental Assessment`, `Completed`
- decision signed date: `2025-05-22`
- frozen review ID: `region1-example-idaho-panhandle-lacy-lemoosh-60853`

## Intent Lock

Lacy Lemoosh is an Idaho Panhandle National Forests example candidate. It is
not a generic Region 1 example, not a substitute for Kootenai or Nez
Perce-Clearwater work, and not evidence that any other forest has a governed
real-package example.

The planned governed identity is:

- `example_id="ipnf-lacy-lemoosh-forest-specific"`
- `review_id="region1-example-idaho-panhandle-lacy-lemoosh-60853"`
- `forest_unit_id="idaho-panhandle-nfs"`
- `applicable_forest_unit_ids=["idaho-panhandle-nfs"]`
- `coverage_slot_id="ipnf-lacy-lemoosh-forest-specific"`
- `coverage_class_id="forest_specific_reviewer_ready"`
- `queue_lineage_source_ids=[]` unless a later workbook-backed Lacy Lemoosh
  queue row is found

`idaho-panhandle-nfs` remains `profile_eval_guidance_only` until package
authority, replay context, forest-plan component/adjudication, compliance, V1
eval, phase eval, and promotion gates pass. Existing Idaho Panhandle queue row
`FOR-022` is project `67684`, not Lacy Lemoosh `60853`.

## Current Evidence

- Live Forest Service readback on 2026-05-29 identifies project `60853` as
  completed, expected analysis type `Environmental Assessment`, forest `Idaho
  Panhandle National Forest`, district `St. Maries Ranger District`, and
  decision signed date `2025-05-22`.
- Live Box readback identifies root folder `Lacy Lemoosh (60853)` under
  `Idaho Panhandle National Forest (110104)` >
  `St Maries Ranger District (11010404)`.
- The Box root exposes `Decision` (`2` files), `Final EA` (`135` files),
  `Draft EA` (`34` files), and `Scoping` (`15` files), totaling `186` listed
  files and `555,066,969` bytes at this level.
- The registry row is still `profile_eval_guidance_only` with
  `primary_example_id=null`; the real-package coverage manifest has no Lacy
  Lemoosh slot.
- `config/forest_plan_profiles.json` has an Idaho Panhandle profile, but this
  packet has not yet proven package-specific district, area, component, or
  supporting-source readiness.

## Goal

Create and close a governed Lacy Lemoosh example package lane as the Idaho
Panhandle primary example only after package authority, review artifacts, eval
contracts, and aggregate gates are present and green.

## Non-Goals

- Do not add Lacy Lemoosh package files or project-specific rows to
  `Document_Register_Master`.
- Do not promote Idaho Panhandle to `real_package_examples_available` before
  package intake, replay context, `v1-ea-eval`, forest-plan component eval,
  and review `phase-eval` pass.
- Do not reroute unrelated Idaho Panhandle queue rows such as `FOR-020` or
  `FOR-022`.
- Do not ratchet aggregate thresholds in Milestone 0.
- Do not weaken tests, eval thresholds, validation checks, or package/component
  coverage to make the packet green.
- Do not stage ignored `source_library/` evidence unless repo policy changes.

## Scope

- Idaho Panhandle Lacy Lemoosh package boundary and review identity
- packet routing, registry guidance, current-state docs, and handoff
- future replay, review eval, applicability adjudication, forest-plan
  component eval, and aggregate coverage contracts
- registry and coverage promotion only after review-readiness gates pass

## Owner Surfaces

- packet: `docs/IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- registry: `config/forest_specific_example_package_registry_v1.json`
- future replay context:
  `config/replay_contexts/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`
- future V1 eval:
  `config/v1_idaho_panhandle_lacy_lemoosh_real_ea_eval.json`
- future component eval:
  `config/forest_plan_component_evals/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`
- future adjudications:
  `config/applicability_adjudications/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`,
  `config/forest_plan_component_adjudications/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`
- future aggregate manifests:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- ignored intake and review outputs:
  `source_library/reviews/_intake/region1-example-idaho-panhandle-lacy-lemoosh-60853/`,
  `source_library/reviews/region1-example-idaho-panhandle-lacy-lemoosh-60853/`
- docs and tests:
  `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`,
  `tests/test_forest_specific_example_package_registry.py`

## Intent Hierarchy

- Invariant: Lacy Lemoosh is only for `idaho-panhandle-nfs` and remains outside
  `Document_Register_Master` unless a separate source-register packet proves
  shared-source promotion.
- Optimization target: keep packet, registry guidance, current routing, tests,
  and handoff aligned on the same forest-qualified identity before intake.
- Acceptable tradeoffs: generated `source_library/` evidence can remain local
  and ignored; Idaho Panhandle can remain profile-guidance-only while open.
- Non-negotiables: do not weaken tests, lower eval thresholds, mark unrelated
  Idaho Panhandle queue rows as Lacy lineage, or reuse the package for another
  forest.

## Weak-Point Prevention Contract

### Weak Point 1

Weak point forecast: Lacy Lemoosh is treated as shared master input.

- Owner surface: workbook, `Document_Register_Master`, queue ledger
- Prevention gate:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_specific_example_package_registry.py`
- Fail threshold: any Lacy Lemoosh package row is added to the master table, or
  unrelated Idaho Panhandle queue rows are resolved as this package
- Future-Codex misuse scenario: a future session treats the Box folder as
  canonical workbook capture instead of a parallel example package

### Weak Point 2

Weak point forecast: Idaho Panhandle is promoted from URL or folder inventory
alone.

- Owner surface: registry, real-package coverage, component coverage
- Prevention gate: review `phase-eval`, V1 eval, component eval,
  `real-package-review-coverage-eval`, and `forest-specific-example-package-eval`
- Fail threshold: Idaho Panhandle leaves `profile_eval_guidance_only`, or a
  Lacy slot becomes required reviewer-ready coverage, before package authority
  and review gates pass
- Future-Codex misuse scenario: a future session adds a registry row after
  downloading files but before deterministic review

### Weak Point 3

Weak point forecast: intake drops `Draft EA` or `Scoping` and reviews only
final decision-core PDFs.

- Owner surface: ignored intake path and replay context
- Prevention gate: package inventory, import manifest, hashes, and `ea-review`
- Fail threshold: intake lacks `Decision`, `Final EA`, `Draft EA`, or
  `Scoping` unless a milestone proves a narrower official replay path
- Future-Codex misuse scenario: a future review misses specialist/supporting
  material because it reviewed only final PDFs

### Weak Point 4

Weak point forecast: forest-plan scope resolves by broad lexical match without
package-specific area or district evidence.

- Owner surface: forest-plan profile, context summary, component contracts
- Prevention gate: `forest-plan-resolve`, component adjudication eval, and
  forest-plan component eval
- Fail threshold: ambiguous scope, missing required source records, unresolved
  mentions, or pending component queue items remain
- Future-Codex misuse scenario: a future session assumes generic "Idaho
  Panhandle" text is enough for reviewer-ready scope

## Milestone Sequence

### Milestone 0 - Open Packet And Freeze Boundary

Outcome label: `resolved`

1. Verify official project and Box root metadata.
2. Freeze the forest-qualified review identity and package URLs.
3. Add this plan and route docs/handoff to it as the active packet.
4. Keep the registry row `profile_eval_guidance_only` and unpromoted.
5. Verify focused tests, aggregate eval, plan lint, and `git diff --check`.

### Milestone 1 - Local Package Authority Intake

Outcome label: `resolved` if the full root inventories and downloads with zero
failures; `reduced` if any official file or folder remains blocked.

Inventory the Box root, preserve folder structure, hash downloaded files, add
the replay context after local authority exists, and run `ea-review` on
`source-set-f70ea11e04ae3d53`.

### Milestone 2 - Forest-Plan Resolver Preflight

Outcome label: `resolved` if scope, source readiness, component inventory, and
adjudication are review-ready; `reduced` if a named Idaho Panhandle blocker
remains.

Build review-local Idaho Panhandle component inventory, run
`forest-plan-resolve`, add only evidence-backed profile vocabulary, and keep
registry/coverage manifests unchanged.

### Milestone 3 - Reviewer Stack Replay

Outcome label: `resolved` if the review reaches reviewer-ready status;
`reduced` if a named applicability, component, compliance, or eval blocker
remains.

Run applicability, generated rule-pack, compliance review, V1 eval,
forest-plan component eval, and review `phase-eval`. Add tracked
eval/adjudication contracts only when generated evidence exists and passes.

### Milestone 4 - Registry And Coverage Promotion

Outcome label: `resolved` for Idaho Panhandle promotion; `reduced` if a
pre-existing aggregate blocker remains outside the Lacy slot.

Add Lacy Lemoosh to real-package coverage, forest-specific registry, and
component-eval coverage only after reviewer-stack gates pass, then rerun the
aggregate gates and update docs/handoff before committing.

## Required Verification Gates

Milestone 0:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md --strict
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_specific_example_package_registry.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
git diff --check
```

Milestone 1:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review --package-path source_library/reviews/_intake/region1-example-idaho-panhandle-lacy-lemoosh-60853 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-idaho-panhandle-lacy-lemoosh-60853 --docling-timeout-seconds 180
PYTHONPATH=src uv run --extra dev pytest tests/test_replay_context.py tests/test_forest_specific_example_package_registry.py
git diff --check
```

Milestones 2-4 add the matching resolver, compliance, V1, component,
`phase-eval`, real-package coverage, forest-specific package, component
coverage, architecture, ruff, compile, and `git diff --check` gates required by
`AGENTS.md` for the touched surfaces.

## Acceptance Criteria

- Lacy Lemoosh has a forest-qualified packet, review ID, and planned example
  identity.
- Idaho Panhandle remains `profile_eval_guidance_only` until promotion gates
  pass.
- Future intake records full official Box roster, hashes, and zero failures
  before replay context is authoritative.
- Forest-plan and reviewer-stack blockers close without relaxed validation.
- Any future promotion updates registry, coverage manifests, eval contracts,
  docs, handoff, and tests in one milestone commit.

## Stop Conditions

- Official Box files cannot be fully inventoried or downloaded.
- The package resolves to a forest other than Idaho Panhandle National Forests.
- Component inventory requires overwriting shared f70 evidence outside this
  packet.
- Reviewer-ready status requires weakening validation, eval thresholds, or
  adjudication gates.
- Lacy Lemoosh appears in registry/coverage slots before review `phase-eval`
  and review-scope aggregate gates pass.

## Closeout Outcome Record

Record each closed milestone with commands run, pass/fail status, skipped
gates, residual risks, docs/handoff updates, and local commit hash.

Milestone 0 closeout on 2026-05-29: plan lint passed; focused registry tests
passed `13/13`; `forest-specific-example-package-eval` passed with
`profile_guidance_only_count=4`, `review_example_count=7`, and
`reviewer_ready_example_count=7`; `git diff --check` passed. Residual risk:
Milestone 1 package-authority intake remains, with no Lacy Lemoosh coverage
slot or primary example yet.

## Gap-Close Verification Addendum

Milestone 0 is gap-closed only while `CURRENT_ROUTING`, `SESSION_HANDOFF`,
`CURRENT_SYSTEM_STATE`, `AGENT_START_HERE`, README, registry guidance, focused
tests, and aggregate eval agree that Lacy Lemoosh is active but unpromoted:
`idaho-panhandle-nfs` stays `profile_eval_guidance_only`,
`primary_example_id=null`, and no Lacy coverage slot exists.
