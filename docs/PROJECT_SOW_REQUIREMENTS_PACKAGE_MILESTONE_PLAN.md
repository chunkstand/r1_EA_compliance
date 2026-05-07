# Project SOW Requirements Package Milestone Plan

Date: 2026-05-06

This milestone builds the upstream planning lane that converts a proposed NEPA action into a
complete resource scope-of-work requirements package. The proving case is the East Crazy
Inspiration Divide Land Exchange because the repo has both a proposed-action record and a completed
EA package with specialist/supporting reports that can be used to calibrate expected resource-area
coverage.

The milestone is scoped to planning requirements before an EA review package exists. It does not
create applicability determinations, compliance findings, legal advice, legal sufficiency
determinations, or final agency decisions.

## Goal

Generate a package that, from a proposed action intake, identifies:

- proposed-action elements on federal land;
- resource areas that must be analyzed;
- evidence supporting each resource-area trigger;
- resource SOW scopes, tasks, data needs, deliverables, and defensibility checks;
- authority-family requirements that inform each scope;
- calibration comparison against completed East Crazies specialist/supporting reports.

The package should make it clear what work is required to prepare a defensible EA for a land
exchange and what information is still missing from the intake.

## Non-Goals

- Do not run downloader, catalog, extraction, review, applicability, generated rule-pack, compliance
  review, phase-eval, or promotion-suite workflows.
- Do not read or write South Plateau review outputs in this branch.
- Do not treat generated SOW scopes as applicability decisions or compliance findings.
- Do not make legal sufficiency or final decision recommendations.
- Do not stage ignored `source_library/` outputs unless repository policy changes explicitly.
- Do not hard-code East Crazies as the only possible land-exchange workflow. East Crazies is the
  calibration fixture, not the architecture boundary.

## Current Branch Boundary

Branch/worktree:

- Branch: `codex/nepa-project-sow-package`
- Worktree: `/Users/chunkstand/projects/usfs-r1-EA-sources-nepa-project-sow-package`

Implemented command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-package \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir source_library
```

Generated local artifact family:

```text
source_library/projects/<project_id>/requirements_package/
  project_sow_package.json
  project_sow_package.md
  project_sow_package_manifest.json
```

The JSON is canonical. Markdown is a rendering from the JSON. `source_library/` remains ignored and
must not be staged.

## Sequence 1: Planning Lane And SOW Package Contract

Status: complete in commit `111d081 Add project SOW package planning lane`.

Purpose: create the first deterministic proposed-action-to-resource-SOW package contract.

Completed surfaces:

- `config/project_sow_resource_scopes_v1.json`
- `config/fixtures/project_sow/east_crazies_land_exchange_intake.json`
- `src/usfs_r1_ea_sources/project_sow_package.py`
- `src/usfs_r1_ea_sources/cli_project_planning.py`
- `src/usfs_r1_ea_sources/cli.py`
- `tests/test_project_sow_package.py`
- `tests/test_cli.py`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/architecture_contract.toml`

Acceptance result:

- The command generated JSON, Markdown, and manifest outputs from the East Crazies proposed-action
  intake.
- The package selected NEPA project management, lands/realty, Forest Plan consistency,
  wildlife/species/botany, cultural/tribal, hydrology/wetlands/water quality,
  roads/access/recreation/designated areas, minerals/hazardous materials, and public involvement
  scopes.
- Validation failed closed on missing required fields, unsupported schema, duplicate scope IDs,
  unknown authority-family IDs, empty selected scope set, or selected scopes lacking SOW content.

## Sequence 2: East Crazies Resource Analysis Comparison

Status: complete in commit `0f3af0c Add East Crazies resource analysis comparison`.

Purpose: use East Crazies as the calibration example by comparing proposed-action-derived resource
areas to the actual specialist/supporting reports produced for the completed package.

Completed surfaces:

- East Crazies intake now includes structured `proposed_action_elements`,
  `resource_analysis_expectations`, and `observed_specialist_reports`.
- Resource-scope config now declares `covered_resource_area_ids`.
- The generated package now includes `resource_analysis_matrix`,
  `observed_specialist_reports`, and `missing_resource_area_requests`.
- Validation now fails if observed specialist/supporting report resource areas are not derived from
  the proposed action or lack selected SOW scope coverage.

East Crazies observed report calibration set:

- `2023 Mineral Potential Report.pdf`
- `2024 Aquatics Report.pdf`
- `2024 At Risk Plants Botany Report.pdf`
- `2024 Carbon Summary.pdf`
- `2024 Cultural Resources.pdf`
- `2024 Recreation Special Areas.pdf`
- `2024 Recreation Special Uses.pdf`
- `2024 Roads Trails Access.pdf`
- `2024 Tribal Relations.pdf`
- `2024 Wetlands Report.pdf`
- `2024 Wildlife Report.pdf`
- `Water Rights Assessment.pdf`
- `Plan Consistency Table.pdf`

Acceptance result:

- CLI smoke selected `10` East Crazies SOW scopes and `23` proposed-action resource areas with
  `0` validation failures.
- Every observed East Crazies report-backed resource area is covered by a selected SOW scope.
- The branch stayed upstream of applicability and compliance review.

## Sequence 3: Intake Evidence Graph

Status: complete.

Purpose: replace flat evidence references with a deterministic, package-local intake evidence graph
that explains why each resource area was triggered and how it is covered by the SOW package.

The graph is a planning artifact. It is not the review evidence graph, not a graph database, and not
a compliance/applicability source of truth.

Target node types:

- `project`
- `proposed_action`
- `action_element`
- `evidence_ref`
- `resource_area`
- `sow_scope`
- `expected_deliverable`
- `observed_specialist_report`

Target edge types:

- `HAS_PROPOSED_ACTION`
- `HAS_ACTION_ELEMENT`
- `SUPPORTED_BY`
- `TRIGGERS_RESOURCE_AREA`
- `COVERED_BY_SOW_SCOPE`
- `REQUIRES_DELIVERABLE`
- `OBSERVED_REPORT_COVERS_RESOURCE_AREA`

Canonical path requirement:

```text
proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope
```

East Crazies calibration requirement:

```text
observed_specialist_report -> resource_area
```

Each observed specialist/supporting report resource area must connect to a resource area that also
has the proposed-action path above.

Implementation surfaces:

- Extend `project_sow_package.py` to build `intake_evidence_graph`.
- Extend the East Crazies intake fixture with evidence refs for proposed-action elements and
  observed reports.
- Emit graph nodes and edges in `project_sow_package.json`.
- Add a concise graph projection to `project_sow_package.md`.
- Add fail-closed validation for missing paths, dangling graph nodes, missing evidence refs, and
  observed report areas without proposed-action support.
- Update `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, and `docs/SESSION_HANDOFF.md`.

Acceptance gate:

- `tests/test_project_sow_package.py` proves every required resource area has the canonical graph
  path.
- Tests prove an observed East Crazies report fails validation when it has no proposed-action
  support path.
- Tests prove a proposed-action element with triggered resource areas but no evidence refs fails
  validation.
- Tests prove duplicate intake-derived graph node IDs fail validation before graph assembly can
  collapse the duplicate records.
- CLI smoke for the East Crazies intake reports `10` SOW scopes, `23` proposed-action resource
  areas, `115` graph nodes, `134` graph edges, and `0` validation failures.
- No applicability decisions, compliance findings, or legal conclusions are introduced.
- Sequence closes as one verified atomic commit.

## Sequence 4: Intake Graph Quality Fixtures

Status: next.

Purpose: harden the graph contract beyond the happy-path East Crazies fixture.

Candidate fixtures:

- missing proposed-action evidence ref;
- observed specialist report with no matching proposed-action resource area;
- proposed-action resource area with no configured SOW scope;
- action element with evidence but no triggered resource area;
- duplicate observed-report IDs or duplicate deliverable graph IDs;
- dangling graph edge;
- land-exchange intake with no federal land action.

Acceptance gate:

- Focused tests cover each failure category.
- Validation messages identify the missing graph path or dangling ID.
- No new runtime special cases are hidden outside config/fixtures and generic graph validation.

## Sequence 5: Reviewer-Facing Package Polish And Optional Rendering

Status: planned after graph quality fixtures.

Purpose: make the package easier for a planning lead or contracting/resource lead to use without
changing the canonical JSON contract.

Candidate work:

- improve Markdown section ordering and tables;
- add an optional PDF rendering from the canonical JSON/Markdown;
- add a compact package summary section for responsible official/resource lead review;
- add a runbook example for creating a new land-exchange intake from a proposed action.

Acceptance gate:

- JSON remains canonical.
- Rendering validation fails if required sections are missing.
- PDF, if added, is generated from the same package JSON and starts with `%PDF-`.
- No ignored generated outputs are staged.

## Required Verification

For implementation sequences touching Python, CLI, config, or generated artifact contracts:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_project_sow_package.py tests/test_cli.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src uv run --extra dev python -m compileall src
PYTHONPATH=src uv run --extra dev python -m json.tool config/project_sow_resource_scopes_v1.json
PYTHONPATH=src uv run --extra dev python -m json.tool config/fixtures/project_sow/east_crazies_land_exchange_intake.json
git diff --check
```

Run a CLI smoke check to `/tmp` before commit:

```bash
rm -rf /tmp/usfs_project_sow_check && \
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources project-sow-package \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir /tmp/usfs_project_sow_check
```

For docs-only plan updates, `git diff --check` is sufficient unless the docs claim new behavior.

## Commit Policy

Each completed sequence should land as one atomic commit on `codex/nepa-project-sow-package`.
Stage only the sequence slice. Leave South Plateau, ignored `source_library/`, and unrelated
worktree changes untouched.

## Stop Conditions

Stop and report instead of patching around the issue if:

- East Crazies observed report coverage cannot be traced from the proposed action;
- a resource area requires an authority family not present in the current authority universe;
- a proposed graph edge would imply applicability or compliance sufficiency;
- implementation would require rerunning large review/compliance workflows;
- generated outputs under `source_library/` would need to be committed.
