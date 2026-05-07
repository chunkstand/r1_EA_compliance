# Project SOW Package Runbook

Use this runbook to create a proposed-action resource SOW requirements package for a new NEPA land
exchange before a complete EA package exists.

The package is planning support only. It does not create applicability decisions, compliance
findings, legal advice, legal sufficiency determinations, or final agency decisions.

## 1. Create The Intake

Start from the minimal land-exchange template when the proposed action is already structured:

```bash
cp config/templates/project_sow_land_exchange_intake_template.json \
  /tmp/new_land_exchange_intake.json
```

The tracked schema for the intake shape is
`docs/schemas/project_sow_intake_v0.schema.json`. The East Crazies fixture remains the calibration
example; it is not the normal starting point for a new proposed action.

If the proposed action exists as plain text, draft an unreviewed intake skeleton first:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-intake-draft \
  --proposed-action /tmp/proposed_action.txt \
  --output /tmp/new_land_exchange_draft_intake.json \
  --forest "Example National Forest" \
  --district "Example Ranger District"
```

Drafted intakes preserve the proposed-action source path, source text hash, paragraph locators, and
candidate resource-area triggers in `draft_metadata`. They are intentionally unreviewed and will not
pass validation until a reviewer confirms the action elements, evidence refs, federal land actions,
resource-area IDs, and clears the draft uncertainty flags. If a draft has validation failures beyond
reviewer confirmation, the draft command reports them in `unexpected_failed_validation_checks` and
returns a failing status.

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

## 4. Run The Proving-Intake Eval

Before treating the project SOW lane as operationally green, run the tracked proving-intake eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-eval \
  --output-dir /tmp/project_sow_eval
```

The default manifest is `config/project_sow_eval_proving_intakes_v1.json`. The eval runs East
Crazies, Red Rock Ridge, and Silver Creek in one command, writes local packages under the selected
output directory, and compares actual metrics and diagnostics to tracked expected values. It keeps
system misses, intake omissions, calibration gaps, and expected no-observed-report cases separate.
It also checks contract-readiness metrics so every selected proving-intake scope must preserve
required deliverables, optional deliverables, and the required contract fields from
`config/project_sow_resource_scopes_v1.json`.

## 5. Add Calibration Reports When Available

If a completed example package exists, populate `observed_specialist_reports[]` with report title,
document role, source record ID, report ID, resource areas, and evidence refs.

Observed reports are calibration evidence only. They do not replace the proposed-action graph path:

```text
proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope
```

## 6. Validate The Intake

Run the validation-only command before package generation:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-intake-validate \
  --intake /tmp/new_land_exchange_intake.json
```

The validation summary reports selected SOW scopes, proposed-action resource-area count, intake
evidence graph node and edge counts, failed validation checks, and `output_written=false`. It does
not create `source_library/projects/<project_id>/requirements_package/`.

The package command can also run the same no-write path:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-package \
  --intake /tmp/new_land_exchange_intake.json \
  --validate-only
```

## 7. Generate The Package

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

JSON is canonical. Markdown and PDF are renderings from the JSON. The generated package is a
planning and contracting support artifact for defining resource SOW needs; it is not a final SOW
award document.

The package renders required and optional deliverables separately. Optional deliverables are planning
visibility only and do not satisfy required deliverable validation. Each selected SOW scope must
also carry assumptions, dependencies, acceptance criteria, reviewer role, review timing, and reviewer
signoff fields from `config/project_sow_resource_scopes_v1.json`.

## 8. Resolve Validation Failures

Common failure categories:

- required intake fields are missing;
- the intake schema version is unsupported;
- nested action element, evidence ref, federal land action, resource expectation, or observed
  report rows are missing required schema fields;
- drafted intake metadata still requires reviewer confirmation;
- a land-exchange intake has no federal land action;
- resource areas do not resolve to a configured SOW scope;
- selected SOW scopes lack required contract fields such as assumptions, dependencies, acceptance
  criteria, reviewer role, review timing, optional deliverables, or reviewer signoff fields;
- selected SOW scopes lack required deliverables, even if optional deliverables are present;
- an action element has resource areas but no evidence refs;
- an action element has evidence refs but no resource areas;
- observed reports cover resource areas not derived from the proposed action;
- proposed-action or observed-report resource areas lack the canonical graph path;
- graph node or edge IDs collide before graph assembly;
- required Markdown or PDF rendering sections are missing.

Do not edit generated `source_library/` outputs by hand. Fix the intake or the tracked resource
scope config, then rerun the command.
