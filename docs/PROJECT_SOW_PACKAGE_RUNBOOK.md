# Project SOW Package Runbook

Use this runbook to create a proposed-action resource SOW requirements package for a new NEPA land
exchange before a complete EA package exists.

The package is planning support only. It does not create applicability decisions, compliance
findings, legal advice, legal sufficiency determinations, or final agency decisions.

## 1. Create The Intake

Start from the East Crazies fixture:

```bash
cp config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  /tmp/new_land_exchange_intake.json
```

Update these required fields:

- `project_id`
- `project_name`
- `forest`
- `districts`
- `project_type`
- `nepa_level`
- `proposed_action_summary`
- `federal_land_actions`

For land exchanges, `federal_land_actions` must identify the federal disposal, acquisition, or
reserved-right action elements taking place on federal land.

## 2. Add Proposed-Action Elements

Each `proposed_action_elements[]` row should contain:

- `action_element_id`
- `description`
- `evidence_refs[]`
- `resource_area_ids[]`
- `resource_indicator_keys[]`

Each evidence-bearing action element must trigger at least one resource area. Each action element
that triggers a resource area must include at least one evidence ref.

## 3. Add Resource Expectations

Populate `resource_analysis_expectations[]` with one row per expected resource area. Each row should
include:

- `resource_area_id`
- `resource_area_name`
- `proposed_action_basis[]`

Resource area IDs must resolve to `covered_resource_area_ids` in
`config/project_sow_resource_scopes_v1.json`.

## 4. Add Calibration Reports When Available

If a completed example package exists, populate `observed_specialist_reports[]` with report title,
document role, source record ID, report ID, resource areas, and evidence refs.

Observed reports are calibration evidence only. They do not replace the proposed-action graph path:

```text
proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope
```

## 5. Generate The Package

Run:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-package \
  --intake /tmp/new_land_exchange_intake.json \
  --output-dir source_library
```

The command writes:

```text
source_library/projects/<project_id>/requirements_package/
  project_sow_package.json
  project_sow_package.md
  project_sow_package.pdf
  project_sow_package_manifest.json
```

JSON is canonical. Markdown and PDF are renderings from the JSON.

## 6. Resolve Validation Failures

Common failure categories:

- required intake fields are missing;
- a land-exchange intake has no federal land action;
- resource areas do not resolve to a configured SOW scope;
- an action element has resource areas but no evidence refs;
- an action element has evidence refs but no resource areas;
- observed reports cover resource areas not derived from the proposed action;
- graph node or edge IDs collide before graph assembly;
- required Markdown or PDF rendering sections are missing.

Do not edit generated `source_library/` outputs by hand. Fix the intake or the tracked resource
scope config, then rerun the command.
