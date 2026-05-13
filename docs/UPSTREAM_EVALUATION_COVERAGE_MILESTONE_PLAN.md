# Upstream Evaluation Coverage Milestone Plan

Date: 2026-05-12

Status: Proposed

Owner context: This is a fresh standalone milestone plan for the upstream reviewer-engine lanes.
It does not replace the broader V1, NEPA 3D, forest-plan, or final-QA plans. It exists to close
one specific weakness: capture, catalog, and extraction are currently guarded mainly by validation
and integrity checks, while the downstream lanes already have explicit eval commands and tracked
fixture sets.

## Purpose

Close the scoped upstream evaluation gap so the repo can fail closed on tricky source-acquisition,
catalog-linking, and extraction regressions by direct eval, not only by structural validation.

For this milestone, "upstream" means:

- workbook-driven capture planning and fetch classification;
- run acceptance and catalog promotion;
- extraction correctness and extraction-admission boundaries.

This milestone is complete only when the scoped upstream lanes have tracked adversarial fixtures,
an executable direct-eval command, aggregate pass/fail reporting, and a governing gate that makes
missing upstream direct-eval coverage visible before promotion.

## Current Evidence

- `docs/OUTPUT_SCHEMAS.md` documents `validate-run`, `catalog_validation.json`,
  `extraction_validation.json`, and `extraction-accuracy-audit` as integrity and validation gates.
- `src/usfs_r1_ea_sources/cli_capture.py` exposes `dry-run`, `preflight`, `download`,
  `validate-run`, `pilot-hosts`, `batch-download`, and `catalog-build`, but no upstream direct-eval
  command.
- `src/usfs_r1_ea_sources/cli_derived.py` exposes `extraction-accuracy-audit`, but that command is
  an artifact-correctness audit over generated outputs, not a tracked gold/adversarial eval suite.
- The repo already has downstream direct-eval surfaces such as `retrieval-eval`, `claim-eval`,
  `rule-claim-eval`, `applicability-eval`, `applicability-gold-eval`, `compliance-review-eval`,
  `compliance-gold-eval`, `forest-plan-component-eval`, and `v1-ea-eval`.
- `tests/test_preflight.py`, `tests/test_validate_run.py`, `tests/test_catalog.py`, and
  `tests/test_extraction_accuracy.py` cover important cases, but they do not currently roll up into
  a tracked upstream eval manifest, category coverage contract, or reviewer-visible upstream
  readiness report.

## Goal

Resolve the scoped upstream evaluation gap for capture, catalog, and extraction by adding a
deterministic direct-eval lane with tracked category coverage, controlled violations, and aggregate
gating.

Completion means all of the following are true:

- the repo has a tracked upstream evaluation contract;
- the contract requires adversarial coverage for the known upstream failure families;
- the eval runs without network access and without broad corpus regeneration;
- the eval summary distinguishes direct-eval coverage from validation coverage;
- the current readiness route fails closed when upstream direct-eval coverage is missing or failing.

## Non-Goals

- Do not expand this milestone into retrieval, claim, rule-claim, applicability, compliance,
  decision-support, final-QA, or NEPA 3D semantics work beyond the narrow gate integration needed
  to surface upstream direct-eval state.
- Do not rewrite downloader, catalog, or extraction architecture unless a small test seam is needed
  for deterministic fixtures.
- Do not rerun broad network capture, full source-set extraction, or review replay workflows as the
  normal proof path.
- Do not treat synthetic upstream eval fixtures as a replacement for live workbook/corpus status.
- Do not stage ignored `source_library/` outputs unless repository policy changes explicitly.

## Scope

- Capture lane: `dry-run`, `preflight`, `validate-run`, and their supporting acceptance/reporting
  logic.
- Catalog lane: `catalog-build`, catalog validation, source-partition promotion behavior, and
  batch-merge integrity surfaces.
- Extraction lane: `extract-build`, `extraction_validation.json`,
  `extraction-accuracy-audit`, extraction-admission boundaries, and extraction fixture coverage.
- New tracked eval config, fixtures, tests, and an aggregate upstream direct-eval command/report.
- Narrow readiness integration so the repo can surface upstream direct-eval status in a durable
  gate instead of leaving it as unit-test-only truth.

## Out Of Scope

- Replacing or weakening the existing validation gates.
- Creating a broad "evaluate every subsystem" umbrella plan in this milestone.
- Adding review-package, forest-plan, or graph fixtures unrelated to the scoped upstream failure
  families.
- Making promotion depend on live network checks.

## Owner Surfaces

- Capture implementation: `src/usfs_r1_ea_sources/dry_run.py`,
  `src/usfs_r1_ea_sources/preflight.py`, `src/usfs_r1_ea_sources/validate_run.py`,
  `src/usfs_r1_ea_sources/cli_capture.py`
- Catalog implementation: `src/usfs_r1_ea_sources/catalog.py`,
  `src/usfs_r1_ea_sources/source_partitions.py`
- Extraction implementation: `src/usfs_r1_ea_sources/extract.py`,
  `src/usfs_r1_ea_sources/extraction_accuracy.py`,
  `src/usfs_r1_ea_sources/extraction_admission.py`,
  `src/usfs_r1_ea_sources/cli_derived.py`
- New eval orchestration: `src/usfs_r1_ea_sources/upstream_evaluation.py`,
  `src/usfs_r1_ea_sources/cli_eval.py`
- Tracked contracts and fixtures: `config/upstream_evaluation_v1.json`,
  `config/fixtures/upstream_eval/`, `tests/fixtures/upstream_eval/`
- Tests: `tests/test_preflight.py`, `tests/test_validate_run.py`,
  `tests/test_catalog.py`, `tests/test_extraction_accuracy.py`,
  `tests/test_upstream_evaluation.py`, `tests/test_architecture_contract.py`
- Docs and handoff: `README.md`, `DOWNLOADER_RULES.md`, `docs/OUTPUT_SCHEMAS.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep direct-eval orchestration in a new `src/usfs_r1_ea_sources/upstream_evaluation.py` owner
  module. Do not spread eval-specific fixture runners across `preflight.py`, `catalog.py`, and
  `extract.py` unless a small reusable seam is required.
- Register the aggregate command in `src/usfs_r1_ea_sources/cli_eval.py` so direct-eval entry
  points stay grouped with other repo eval commands instead of fragmenting command ownership.
- Keep existing validation commands as producers of structural truth. Do not rename them as evals.
- Put tracked deterministic inputs under `config/fixtures/upstream_eval/` or
  `tests/fixtures/upstream_eval/`; do not depend on mutable local `source_library/` state for the
  core eval categories.
- If a readiness integration is needed, prefer extending `phase-eval` with a clearly named
  `upstream_evaluation` phase rather than inventing a second unrelated promotion route.
- Create a tracked evaluation coverage register at `docs/EVALUATION_COVERAGE_REGISTER.md` and use
  it as the durable index for direct-eval coverage status by subsystem.

## Weak-Point Prevention Contract

- Weak point forecast: the new "eval" lane simply re-reports existing validation booleans, so the
  original gap survives behind new names.
  Owner surface: `src/usfs_r1_ea_sources/upstream_evaluation.py`,
  `config/upstream_evaluation_v1.json`, `tests/test_upstream_evaluation.py`
  Prevention gate: the upstream eval manifest must declare required adversarial categories,
  controlled-violation cases, and minimum negative-case counts by lane.
  Fail threshold: the aggregate eval passes when a category is missing or when all cases are
  positive-path only.
  Controlled violation: remove one required category from the manifest and mutate one negative case
  into a false pass; the eval must fail.
  Future-Codex misuse scenario: a later session wraps `validate-run` and calls it "upstream eval";
  the manifest/category gate must fail before that lands.

- Weak point forecast: fixture coverage becomes East-Crazies-specific or workbook-row-specific
  instead of lane-general and reusable.
  Owner surface: `config/fixtures/upstream_eval/`, `tests/fixtures/upstream_eval/`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`
  Prevention gate: fixture naming and manifest categories must describe failure families, not one
  project or one review ID.
  Fail threshold: a required category can only be proved by a review-local package or by active
  `source_library/` state.
  Controlled violation: point a required category at a review-local artifact outside the fixture
  tree; the eval loader must reject it.
  Future-Codex misuse scenario: a later session plugs a one-off East Crazies artifact into the
  upstream eval to get green faster; fixture path validation must fail.

- Weak point forecast: OCR/table/appendix extraction cases are silently skipped because they are
  harder than HTML and XML.
  Owner surface: `config/upstream_evaluation_v1.json`,
  `src/usfs_r1_ea_sources/extraction_accuracy.py`, `tests/test_extraction_accuracy.py`,
  `tests/test_upstream_evaluation.py`
  Prevention gate: the manifest must require explicit extraction adversarial categories for OCR,
  table-dense layout, appendix content, and section-boundary extraction.
  Fail threshold: extraction direct-eval passes without those categories.
  Controlled violation: drop the OCR or section-boundary category from the manifest; the aggregate
  eval must fail on missing required coverage.
  Future-Codex misuse scenario: a later session keeps only easy born-digital PDF cases; the
  coverage register and manifest thresholds must expose the reduction.

- Weak point forecast: docs and readiness gates drift, leaving operators unable to tell whether a
  green upstream lane came from validation only or from direct eval plus validation.
  Owner surface: `docs/OUTPUT_SCHEMAS.md`, `README.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`, `docs/SESSION_HANDOFF.md`, `src/usfs_r1_ea_sources/evidence_graph.py`
  Prevention gate: docs closeout plus the readiness integration must name direct-eval coverage
  separately from validation coverage.
  Fail threshold: the milestone lands without one durable document that says which upstream lanes
  have direct eval and which still rely only on validation.
  Controlled violation: remove the register update or the `phase-eval` wiring during closeout;
  acceptance must fail.
  Future-Codex misuse scenario: a later session updates the tests only and forgets the operator
  truth surface; docs and readiness checks must catch it.

## Milestone Sequence

### Sequence 0 - Contract The Upstream Eval Coverage Before New Command Logic

Outcome label: reduced

Purpose: define what counts as upstream direct-eval coverage before implementing the command.

Implementation tasks:

1. Add `config/upstream_evaluation_v1.json` with:
   - required lane families;
   - required category IDs;
   - minimum positive and controlled-violation counts;
   - expected owner surfaces;
   - output schema expectations for the aggregate summary.
2. Add `docs/EVALUATION_COVERAGE_REGISTER.md` with at least the upstream rows:
   `preflight`, `validate_run`, `catalog_validation`, `extraction_accuracy`,
   each marked as `direct_eval_missing` at baseline and naming current validation gates.
3. Add a failing-or-baseline test file `tests/test_upstream_evaluation.py` that proves the
   aggregate loader rejects missing categories and empty negative coverage.

Required category families in the initial contract:

- `challenge_page_http200`
- `not_found_body_http200`
- `duplicate_url_row_preservation`
- `duplicate_content_canonical_link`
- `url_override_provenance_drift`
- `batch_ledger_manifest_mismatch`
- `catalog_partition_or_not_in_run_drift`
- `ocr_heavy_pdf_extraction`
- `table_dense_pdf_extraction`
- `appendix_content_extraction`
- `section_boundary_extraction`

Acceptance signals:

- The repo has a tracked upstream eval manifest and coverage register.
- Missing required categories fail the new test surface.
- The contract distinguishes direct eval from validation.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_upstream_evaluation.py tests/test_architecture_contract.py
git diff --check
```

Stop conditions:

- The contract cannot express required categories without depending on live network state.
- The design can only work by renaming existing validation outputs as eval outputs.

### Sequence 1 - Add Capture And Acceptance-Gate Adversarial Eval Coverage

Outcome label: reduced

Purpose: turn the capture lane from unit-tested edge handling into tracked direct-eval coverage.

Implementation tasks:

1. Add deterministic capture fixtures covering:
   - challenge page returned with `200`;
   - deceptive `200` "document not found" body;
   - duplicate URL row preservation with one fetch and multiple manifest rows;
   - duplicate-content canonical-link integrity;
   - URL-override provenance drift;
   - batch/download acceptance-gate mismatches.
2. Implement aggregate-case runners in `upstream_evaluation.py` that invoke existing capture and
   acceptance functions with fixture-controlled fetchers and manifests.
3. Report per-category pass/fail counts, failure reasons, and controlled-violation outcomes in a
   deterministic `upstream_evaluation_results.json`.
4. Keep `tests/test_preflight.py` and `tests/test_validate_run.py` as focused unit tests; do not
   move their logic into the new aggregate tests.

Acceptance signals:

- The aggregate upstream eval runs the required capture and `validate-run` families without network.
- Each required family has at least one expected pass case and one controlled violation.
- The output shows category counts, pass counts, and exact failing case IDs when red.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_preflight.py tests/test_validate_run.py tests/test_upstream_evaluation.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json --results-dir /tmp/usfs-upstream-eval
git diff --check
```

Stop conditions:

- The fixture path requires live workbook download traffic instead of synthetic/local inputs.
- The eval only asserts `validation_passed=true` and cannot prove the adversarial cases directly.

### Sequence 2 - Add Catalog And Extraction Adversarial Eval Coverage

Outcome label: reduced

Purpose: close the same direct-eval gap for catalog promotion and extraction accuracy.

Implementation tasks:

1. Add deterministic catalog fixtures for:
   - `not_in_run` and source-partition drift;
   - batch-ledger/manifest mismatch;
   - supplemental source-delta role or primary-plan classification drift;
   - reviewer-field/linking regressions that validation should catch.
2. Add deterministic extraction fixtures for:
   - OCR-heavy PDF text admission;
   - table-dense PDF extraction;
   - appendix-content retention;
   - section-boundary correctness for scoped XML or equivalent boundary-sensitive text;
   - markup leakage and text/chunk mismatch controlled violations.
3. Reuse `extraction-accuracy-audit` checks where they remain the correct producer of structural
   truth, but add direct-eval case definitions that prove the failure families are intentionally
   covered.
4. Extend the coverage register so catalog and extraction rows can move from
   `direct_eval_missing` to `direct_eval_present` only when the aggregate eval passes their required
   category counts.

Acceptance signals:

- Catalog and extraction families are part of the tracked upstream eval manifest.
- OCR/table/appendix/boundary categories are explicit and enforced.
- Aggregate output separates capture, catalog, and extraction lane coverage.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_extraction_accuracy.py tests/test_extract.py tests/test_upstream_evaluation.py tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json --results-dir /tmp/usfs-upstream-eval
git diff --check
```

Stop conditions:

- Required OCR/table/appendix cases cannot be represented with small tracked fixtures and need a
  separate binary-fixture minimization preflight.
- Extraction "coverage" can only be claimed by reading active ignored `source_library/` outputs.

### Sequence 3 - Wire The Aggregate Upstream Eval Into Readiness And Closeout Docs

Outcome label: resolved

Purpose: make the scoped gap visibly closed in the repo's governing readiness surfaces.

Implementation tasks:

1. Add `upstream-eval` to `src/usfs_r1_ea_sources/cli_eval.py`.
2. Write a stable aggregate output family, preferably:
   - `source_library/evaluations/upstream/upstream_evaluation_results.json`
   - `source_library/evaluations/upstream/upstream_evaluation_report.md`
3. Extend `phase-eval` with a clearly named `upstream_evaluation` phase that reads the aggregate
   summary when present and fails closed when required upstream coverage is missing or failing.
4. Update `README.md`, `DOWNLOADER_RULES.md`, `docs/OUTPUT_SCHEMAS.md`,
   `docs/CURRENT_SYSTEM_STATE.md`, and `docs/EVALUATION_COVERAGE_REGISTER.md` so they distinguish:
   - structural validation;
   - direct upstream eval coverage;
   - remaining lanes still awaiting broader direct-eval work.
5. Update `docs/SESSION_HANDOFF.md` with the closeout command set, output paths, residual risks,
   and the next milestone boundary.

Acceptance signals:

- The repo has one durable upstream direct-eval command and one durable upstream coverage register.
- `phase-eval` exposes upstream direct-eval state separately from validation-only state.
- The scoped upstream gap is marked `resolved` in the register only when the required categories,
  controlled violations, and aggregate gate are all green.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_preflight.py tests/test_validate_run.py tests/test_catalog.py tests/test_extraction_accuracy.py tests/test_upstream_evaluation.py tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json --results-dir source_library/evaluations/upstream
git diff --check
```

Stop conditions:

- The only way to surface upstream direct-eval readiness is to invent a second promotion path that
  conflicts with `phase-eval`.
- The documentation cannot clearly distinguish validation from direct eval after implementation.

## Required Implementation Artifacts

- `config/upstream_evaluation_v1.json`
- `config/fixtures/upstream_eval/`
- `tests/fixtures/upstream_eval/`
- `src/usfs_r1_ea_sources/upstream_evaluation.py`
- `tests/test_upstream_evaluation.py`
- focused updates to `tests/test_preflight.py`, `tests/test_validate_run.py`,
  `tests/test_catalog.py`, `tests/test_extraction_accuracy.py`
- `src/usfs_r1_ea_sources/cli_eval.py`
- narrow `phase-eval` integration in `src/usfs_r1_ea_sources/evidence_graph.py`
- `docs/EVALUATION_COVERAGE_REGISTER.md`

## Required Documentation And Handoff Updates

- `README.md`
- `DOWNLOADER_RULES.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/EVALUATION_COVERAGE_REGISTER.md`
- `docs/SESSION_HANDOFF.md`
- this milestone plan with implementation status and closeout evidence

## Required Verification Gates

- Focused upstream tests:
  `tests/test_preflight.py`, `tests/test_validate_run.py`, `tests/test_catalog.py`,
  `tests/test_extract.py`, `tests/test_extraction_accuracy.py`, `tests/test_upstream_evaluation.py`
- CLI and boundary registration:
  `tests/test_architecture_contract.py`
- Static quality:
  `PYTHONPATH=src uv run --extra dev ruff check src tests`
- Syntax safety:
  `PYTHONPATH=src python -m compileall src`
- Aggregate direct-eval replay:
  `PYTHONPATH=src python -m usfs_r1_ea_sources upstream-eval --manifest config/upstream_evaluation_v1.json`
- Docs consistency:
  `git diff --check`

## Acceptance Criteria

- The milestone creates a tracked upstream evaluation contract and coverage register.
- The contract requires all named upstream adversarial categories and fails when one is absent.
- The aggregate upstream eval runs without network access and without broad `source_library/`
  regeneration.
- Each required upstream category has at least one expected pass case and one controlled violation.
- Capture, catalog, and extraction each move from validation-only to direct-eval-backed status in
  `docs/EVALUATION_COVERAGE_REGISTER.md`.
- The aggregate output reports lane coverage counts, failed case IDs, controlled-violation results,
  and overall `passed`.
- `phase-eval` exposes `upstream_evaluation` separately from structural validation.
- No existing validation gate is weakened or deleted to make the new direct-eval lane pass.
- The closeout commit includes implementation, fixtures, tests, docs, and handoff updates for this
  milestone only.

## Stop Conditions

- A required category can only be proved by live network behavior rather than deterministic
  fixtures.
- Fixture requirements would force the repo to add oversized binary artifacts without a separate
  minimization decision.
- The implementation relies on workbook- or review-specific heuristics instead of tracked category
  coverage.
- Any proposed change weakens existing validation checks or narrows existing failure detection just
  to produce a green result.

## Local Commit Closeout Policy

- Stage only the verified upstream-evaluation slice.
- Leave unrelated dirty or untracked files alone, including existing viewer and draft-artifact
  changes outside this milestone.
- Include code, fixtures, tests, docs, the coverage register, and handoff updates in the same local
  atomic commit.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the milestone as incomplete until the local commit exists and the required verification
  commands are green.

## Residual Risks And Next Milestone Routing

- This milestone resolves the scoped upstream evaluation gap only for capture, catalog, and
  extraction. It does not resolve the separate downstream thin-coverage issues in retrieval, claim,
  compliance-review seed breadth, decision-support fixture diversity, or NEPA 3D task-style graph
  evaluation.
- If this milestone closes green, the next evaluation-strengthening milestone should target the
  thin direct-eval breadth in retrieval, claim, rule-claim, and compliance-review fixtures rather
  than reopening upstream capture/extraction work.
