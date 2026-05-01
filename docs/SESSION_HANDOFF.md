# Session Handoff

Date: 2026-05-01

## Current State

The forest-plan review evaluator now runs component-evaluation V0 by default for packages resolved
to the selected forest-plan profile. The worktree was clean before this milestone began; these
changes remain unstaged and uncommitted until the operator asks for commit work.

Current session update:

- Forest-plan component evaluation V0 has been added as a required `forest-plan-resolve` stage for
  packages resolved to the selected forest-plan profile; `--forest-plan-component-inventory-path`
  only overrides the inventory path.
- New component outputs are `forest_plan_component_findings.json`,
  `forest_plan_component_findings.md`, and `forest_plan_reviewer_resolution_queue.json`.
- `config/forest_plan_component_inventory_seed.json` contains the first narrow Custer Gallatin seed
  inventory for East Crazies-relevant Crazy Mountains Backcountry Area components.
- Component validation now fails closed on source-set drift, requires supported/partial findings to
  carry both package and plan-source evidence, and turns missing package evidence into
  reviewer-resolution queue items.
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

Implemented behavior:

- `config/forest_plan_profiles.json` contains the first forest-plan profile for Custer Gallatin.
- `forest-plan-resolve` reads forest names, ambiguous terms, required source records, area terms,
  overlays, and supporting evidence routes from the selected profile.
- `forest-plan-resolve` writes component findings, a Markdown rendering, and a reviewer-resolution
  queue from a data inventory for packages resolved to the selected forest-plan profile.
- `config/forest_plan_component_inventory_seed.json` is the current component inventory seed for
  the Crazy Mountains Backcountry Area proving slice.
- Default Custer Gallatin V0 output compatibility is preserved: `scope_status` still uses
  `custer_gallatin`, `not_custer_gallatin`, or `ambiguous`.
- `--forest-unit-id` and `--forest-plan-profiles-path` allow the resolver to run against another
  configured profile path.
- Other configured profiles are treated as known out-of-scope forests when Custer Gallatin is the
  selected profile.
- Default profile loading works from outside the repository working directory.

Latest verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/forest_plan_profiles.json /tmp/forest_plan_profiles.validated.json
python -m json.tool config/forest_plan_component_inventory_seed.json /tmp/forest_plan_component_inventory_seed.validated.json
git diff --check
```

Results: full test suite passed with `167 passed`; focused resolver/profile tests passed with
`29 passed`; lint, compile, JSON validation, and whitespace checks passed.

## Next Sequence

Sequence 4 continuation: run the improved forest-plan resolver plus the component inventory against
the local East Crazies/Custer Gallatin demo package and decide whether the V1 demo uses
`forest-plan-resolve` plus `ea-review`, or also includes `compliance-review`.

Goal:
Prove the first real proving case resolves through profile data, not Custer Gallatin-specific
runtime constants or East Crazies-specific exceptions.

Non-goals:

- Do not rebuild the full 190-row downstream corpus.
- Do not add East Crazies-specific resolver branches.
- Do not scan raw artifact filenames to decide forest-plan behavior.
- Do not broaden the output schema unless the fixture requires a minimal test-only assertion.

Relevant files:

- `docs/FOREST_PLAN_REVIEW_EVALUATOR_V1.md`
- `docs/V1_DEMO_DOCUMENT_REVIEW_MILESTONE_PLAN.md`
- `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`
- `config/forest_plan_profiles.json`
- `config/forest_plan_component_inventory_seed.json`
- `src/usfs_r1_ea_sources/forest_plan_components.py`
- `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `tests/test_forest_plan_resolver.py`
- Optional new fixture file under `tests/fixtures/` if a durable text fixture is cleaner than an
  inline package string.

Required eval signal:

- The package resolves to `scope_status=custer_gallatin` through selected profile names.
- The package resolves the Bridger, Bangtail, and Crazy Mountains Geographic Area.
- The package resolves the Crazy Mountains Backcountry Area.
- Required Custer Gallatin profile source records are present in retrieval readiness.
- FEIS, Biological Assessment, and Biological Opinion routes trigger only from explicit package
  evidence.
- ROD evidence does not trigger from generic decision labels unless explicit ROD terms are present.
- Reviewer-ready status remains citation/evidence gated.
- Component findings are produced from the inventory path with plan-source evidence, package
  evidence where present, and reviewer-resolution items for gaps.
- Stale component inventory source-set IDs fail closed.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/forest_plan_component_inventory_seed.json /tmp/forest_plan_component_inventory_seed.validated.json
git diff --check
```

Run the full suite before committing if resolver behavior changes beyond fixture construction.

Commit policy:
Stage only the component-evaluation milestone files, verify, and commit only when the operator asks
for a commit.

Stop conditions:

- The fixture cannot prove profile-driven behavior without adding a special East Crazies runtime
  branch.
- Required source-record readiness fails because the test source library lacks a profile-required
  supporting record.
- A finding or reviewer-ready status would pass without both package evidence and source-library
  evidence.

Expert alignment check for Sequence 4:

- Scott Vandegrift: readiness and reuse should be explicit; avoid unnecessary full-corpus rebuilds.
- Chuck Nicholson: the fixture should look like practitioner QA/QC, with transparent criteria and
  actionable gaps.
- Liz Esposito: every supported result must keep source-record IDs and evidence basis visible; do
  not convert the fixture into a legal conclusion.
