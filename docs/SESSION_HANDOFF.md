# Session Handoff

Date: 2026-05-01

## Current State

The forest-plan review harness is in the profile-driven resolver milestone. The worktree was clean
before this handoff was written.

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
- Default Custer Gallatin V0 output compatibility is preserved: `scope_status` still uses
  `custer_gallatin`, `not_custer_gallatin`, or `ambiguous`.
- `--forest-unit-id` and `--forest-plan-profiles-path` allow the resolver to run against another
  configured profile path.
- Other configured profiles are treated as known out-of-scope forests when Custer Gallatin is the
  selected profile.
- Default profile loading works from outside the repository working directory.

Latest verification from the Sequence 2 hardening commit:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py tests/test_reuse_inventory.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/forest_plan_profiles.json /tmp/forest_plan_profiles.validated.json
git diff --check
```

Results: full test suite passed with `163 passed`; focused resolver/profile/reuse tests passed with
`27 passed`; lint, compile, JSON validation, and whitespace checks passed.

## Next Sequence

Sequence 3: add East Crazies fixture coverage for the profile-driven resolver path.

Goal:
Prove the first real proving case resolves through profile data, not Custer Gallatin-specific
runtime constants or East Crazies-specific exceptions.

Non-goals:

- Do not rebuild the full 190-row downstream corpus.
- Do not add East Crazies-specific resolver branches.
- Do not scan raw artifact filenames to decide forest-plan behavior.
- Do not broaden the output schema unless the fixture requires a minimal test-only assertion.

Relevant files:

- `docs/FOREST_PLAN_REVIEW_HARNESS_V1.md`
- `config/forest_plan_profiles.json`
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

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Run the full suite before committing if resolver behavior changes beyond fixture construction.

Commit policy:
Stage only the Sequence 3 files, verify, and commit before starting Sequence 4.

Stop conditions:

- The fixture cannot prove profile-driven behavior without adding a special East Crazies runtime
  branch.
- Required source-record readiness fails because the test source library lacks a profile-required
  supporting record.
- A finding or reviewer-ready status would pass without both package evidence and source-library
  evidence.

Expert alignment check for Sequence 3:

- Scott Vandegrift: readiness and reuse should be explicit; avoid unnecessary full-corpus rebuilds.
- Chuck Nicholson: the fixture should look like practitioner QA/QC, with transparent criteria and
  actionable gaps.
- Liz Esposito: every supported result must keep source-record IDs and evidence basis visible; do
  not convert the fixture into a legal conclusion.

