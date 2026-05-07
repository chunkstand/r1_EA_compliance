# Project SOW Operationalization Milestone Plan

Date: 2026-05-07

This milestone operationalizes the project SOW requirements package generator after the East
Crazies proving implementation. The current generator can produce a canonical JSON package plus
Markdown and PDF renderings from a structured `project-sow-intake-v0` file. Operationalization means
making that workflow repeatable for new NEPA land-exchange proposed actions without hand-editing the
large East Crazies fixture as the normal intake path.

This plan is a successor to `docs/PROJECT_SOW_REQUIREMENTS_PACKAGE_MILESTONE_PLAN.md`. That earlier
plan proves the package contract, intake evidence graph, graph-quality validation, and
reviewer-facing renderings. This plan turns the proved generator into a planner-usable workflow.

## Goal

Make the project SOW generator operational for repeated land-exchange planning work:

- create and validate new project intakes without copying a large calibration fixture by hand;
- preserve the deterministic proposed-action path
  `proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope`;
- produce contract-ready resource SOW packages that are reviewer-readable and machine-auditable;
- separate unresolved resource areas, calibration gaps, intake defects, and reviewer decisions;
- compare generated scopes against more than one proving project before treating the workflow as
  operationally ready;
- define the downstream handoff from SOW package to EA package assembly without creating
  applicability decisions, compliance findings, legal advice, legal sufficiency conclusions, or
  final agency decisions.

## Non-Goals

- Do not run downloader, catalog, extraction, applicability, generated rule-pack, compliance review,
  phase-eval, or promotion-suite workflows as part of this operationalization milestone unless a
  later sequence explicitly adds a bounded handoff smoke.
- Do not read or write South Plateau review outputs in this branch.
- Do not treat SOW scope selection as authority applicability, compliance sufficiency, or legal
  sufficiency.
- Do not hide land-exchange resource logic in runtime branches. Domain knowledge belongs in tracked
  schema, resource-scope config, fixtures, eval cases, and reviewer-visible outputs.
- Do not stage generated `source_library/` packages unless repository policy changes explicitly.

## Current Baseline

Current branch/worktree:

- Branch: `codex/nepa-project-sow-package`
- Worktree: `/Users/chunkstand/projects/usfs-r1-EA-sources-nepa-project-sow-package`

Implemented command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-package \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir source_library
```

Current generated artifact family:

```text
source_library/projects/<project_id>/requirements_package/
  project_sow_package.json
  project_sow_package.md
  project_sow_package.pdf
  project_sow_package_manifest.json
```

Current East Crazies accepted smoke signal:

- `10` selected SOW scopes;
- `23` proposed-action resource areas;
- `115` intake evidence graph nodes;
- `134` intake evidence graph edges;
- `0` validation failures;
- valid `%PDF-` header.

## Operational Readiness Definition

The generator is operationally ready when all of the following are true:

- a new land-exchange proposed action can start from a small intake template or generated draft, not
  by editing the full East Crazies fixture;
- intake validation can run without writing package outputs;
- resource-area IDs, action elements, evidence refs, observed report calibration rows, and reviewer
  adjudications have documented schemas and focused failure messages;
- at least three proving intakes run through the package generator and eval harness;
- generated resource scopes include contract-ready assumptions, optional vs required deliverables,
  dependencies, acceptance criteria, and reviewer signoff fields;
- reviewer adjudication decisions are captured as tracked or generated artifacts with deterministic
  replay;
- the downstream EA package assembly handoff is explicit and does not cross into applicability or
  compliance review;
- the operational smoke/eval command is boringly green before any milestone closeout commit.

## Sequence 1: Intake Schema, Template, And Validation-Only Command

Status: complete.

Purpose: remove the largest operational friction point: hand-authoring a full structured intake
from the East Crazies fixture.

Implemented work:

- added `docs/schemas/project_sow_intake_v0.schema.json` for `project-sow-intake-v0`;
- added `config/templates/project_sow_land_exchange_intake_template.json` as the minimal
  land-exchange starting template;
- added `project-sow-intake-validate` plus `project-sow-package --validate-only`, both of which
  validate without writing `source_library/` outputs;
- validation summaries now report required-field, federal land action, action element, evidence
  ref, resource-area, observed-report, selected-scope, and canonical graph path checks with
  `output_written=false`;
- validation now fails closed on schema-shape defects in nested action-element, evidence-ref,
  federal-land-action, resource-expectation, and observed-report rows instead of relying only on
  graph construction side effects;
- `docs/PROJECT_SOW_PACKAGE_RUNBOOK.md` now documents the template-first validation workflow.

Acceptance gate status:

- minimal template validates with `4` selected SOW scopes, `2` proposed-action resource areas,
  `0` validation failures, and no generated outputs;
- invalid intake tests fail closed on missing federal land action, missing action elements, missing
  or incomplete evidence refs, incomplete observed report rows, unknown resource-area IDs, and
  unsupported schema version;
- the East Crazies intake validates with the accepted counts: `10` selected SOW scopes, `23`
  proposed-action resource areas, `115` graph nodes, `134` graph edges, and `0` validation failures;
- validation-only runs keep generated `source_library/` package outputs unwritten;
- docs and handoff identify validation from the minimal template as the supported first
  operational step.

## Sequence 2: Intake Authoring Assistant For Proposed Actions

Status: complete.

Purpose: create a repeatable path from a proposed-action narrative to structured intake rows while
keeping human review in control.

Implemented work:

- added `project-sow-intake-draft` to draft an unreviewed intake skeleton from a plain-text
  proposed action file;
- added `config/project_sow_intake_draft_rules_v1.json` so federal-action and resource-area
  candidate extraction stays in tracked data rather than hidden runtime branches;
- draft output preserves the proposed-action source path, source text hash, paragraph locators, and
  source title in `draft_metadata` and evidence refs;
- draft metadata records `review_status=unreviewed`, `reviewer_confirmation_required=true`, and
  uncertainty flags so the draft cannot be used as package input until reviewer confirmation clears
  those fields;
- added proposed-action text fixtures for a land-exchange draft and an ambiguity case, plus
  expected draft metadata for the positive fixture;
- added runbook examples for drafting, reviewer confirmation, validation, and package generation.

Completed first pass:

- define the draft-intake artifact contract, uncertainty flags, and reviewer-confirmation boundary;
- add one proposed-action text fixture plus expected draft-intake metadata without attempting a
  broad parser;
- keep the draft output upstream of package generation until `project-sow-intake-validate` passes.

Acceptance gate status:

- draft generation produces a `project-sow-intake-v0` artifact with `draft_metadata` schema version
  `project-sow-intake-draft-v0`, but validation fails on
  `draft_reviewer_confirmation_complete` until reviewer confirmation is explicit;
- generated drafts mark candidate resource areas, candidate federal land actions, source locators,
  and uncertainty flags as review work, not as accepted SOW decisions;
- tests cover the Red Rock Ridge proposed-action fixture, an ambiguous land-adjustment fixture, and
  a reviewer-confirmed draft replay;
- draft output includes no applicability decision, compliance finding, legal advice, legal
  sufficiency conclusion, or final agency decision.

## Sequence 3: Multi-Project Calibration And Eval Harness

Status: planned.

Purpose: stop treating East Crazies as the only quality signal.

Candidate work:

- add at least two additional land-exchange or closely adjacent NEPA proposed-action fixtures;
- for each proving intake, record expected resource-area coverage and available observed specialist
  reports when a completed package exists;
- add a `project-sow-eval` command or test harness that runs all proving intakes and reports scope
  counts, graph path coverage, unresolved areas, calibration gaps, and rendering checks;
- track accepted expected metrics in a config or fixture file instead of hard-coding them in tests.

Acceptance gate:

- at least three proving intakes run in one command;
- each proving intake has complete canonical graph paths for expected resource areas;
- eval output distinguishes system misses, intake omissions, calibration gaps, and expected
  no-observed-report cases;
- East Crazies remains green at `10` scopes, `23` proposed-action resource areas, `115` graph nodes,
  `134` graph edges, and `0` validation failures.

## Sequence 4: Contract-Ready Resource SOW Content

Status: planned.

Purpose: make resource scopes usable by a planning lead or contracting/resource lead, not merely
machine-valid.

Candidate work:

- extend `config/project_sow_resource_scopes_v1.json` with contract-oriented fields such as
  assumptions, dependencies, optional deliverables, required deliverables, acceptance criteria,
  reviewer role, and review timing;
- render those fields into JSON, Markdown, and PDF without changing JSON canonicality;
- make required vs optional deliverables explicit;
- add tests that fail if a selected SOW scope lacks required contracting fields.

Acceptance gate:

- every selected scope in East Crazies has tasks, data needs, required deliverables, defensibility
  checks, assumptions, dependencies, and acceptance criteria;
- optional deliverables are visible but do not satisfy required deliverable gates;
- Markdown/PDF renderings surface the contract-ready fields without burying the reviewer summary;
- docs identify the package as a planning/contracting support artifact, not a final SOW award
  document.

## Sequence 5: Reviewer Adjudication Loop

Status: planned.

Purpose: make unresolved resource areas and calibration gaps reviewable and replayable.

Candidate work:

- generate a reviewer worklist for unresolved resource areas, missing evidence refs, unknown
  resource-area IDs, calibration gaps, and optional deliverable decisions;
- define an adjudication template with accepted, rejected, needs-information, and out-of-scope
  decisions;
- add an apply/replay command that updates package generation inputs or overlays without
  hand-editing generated outputs;
- preserve reviewer identity/date/source in the adjudication artifact.

Acceptance gate:

- unresolved or calibration-gap rows can be exported to a worklist;
- applying an adjudication artifact changes package status deterministically;
- invalid adjudication rows fail with targeted messages;
- adjudication artifacts do not create applicability decisions, compliance findings, legal advice,
  legal sufficiency conclusions, or final agency decisions.

## Sequence 6: Downstream EA Package Assembly Handoff

Status: planned.

Purpose: define how an accepted SOW package becomes the starting checklist for assembling a
defensible EA package.

Candidate work:

- add a handoff artifact that maps SOW scopes to expected future EA package documents or evidence
  slots;
- distinguish source collection, specialist report production, public involvement, consultation,
  Forest Plan consistency, and decision-record support;
- document what downstream commands may consume later and what they must not infer;
- add an optional dry-run handoff command that reads a package JSON and emits the expected EA
  package assembly checklist.

Acceptance gate:

- handoff output is derived from canonical `project_sow_package.json`;
- the handoff identifies expected future artifacts without requiring them to exist yet;
- downstream boundaries are explicit: no applicability review, generated rule pack, compliance
  review, or legal sufficiency claim is triggered by SOW generation;
- tests prove the handoff remains stable for East Crazies.

## Sequence 7: Operational Gate And Release Closeout

Status: planned.

Purpose: define one boring operational readiness command and close the milestone only when it is
green.

Candidate work:

- add a single documented operational verification command or script that runs intake validation,
  proving-intake evals, package generation, rendering checks, and docs/schema checks;
- write an operational readiness report under tracked eval artifacts or docs;
- update README, output schemas, runbook, current-state docs, and session handoff;
- decide whether the operationalized command should remain local-only or be included in broader CI.

Acceptance gate:

- operational gate passes for all proving intakes;
- docs and schemas match the implemented artifacts;
- ignored generated outputs remain unstaged;
- milestone closes as one verified sequence commit after all prior sequence commits are green.

## Required Verification

For implementation sequences touching Python, CLI, config, schema, or generated artifact contracts:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_project_sow_package.py tests/test_cli.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src uv run --extra dev python -m compileall src
PYTHONPATH=src uv run --extra dev python -m json.tool docs/schemas/project_sow_intake_v0.schema.json
PYTHONPATH=src uv run --extra dev python -m json.tool config/templates/project_sow_land_exchange_intake_template.json
PYTHONPATH=src uv run --extra dev python -m json.tool config/project_sow_resource_scopes_v1.json
PYTHONPATH=src uv run --extra dev python -m json.tool config/fixtures/project_sow/east_crazies_land_exchange_intake.json
git diff --check
```

For docs-only plan updates:

```bash
git diff --check
```

For operational milestone closeout, also run the final operational gate introduced by Sequence 7.

## Stop Conditions

Stop and report instead of continuing if:

- a proposed implementation would require mutating ignored `source_library/` evidence as a tracked
  artifact;
- the intake draft path would create unreviewed legal, applicability, or compliance conclusions;
- a new proving fixture contradicts the current resource-scope taxonomy enough that the taxonomy
  needs a separate design pass;
- the work would cross into South Plateau or other active review outputs outside this branch
  boundary.
