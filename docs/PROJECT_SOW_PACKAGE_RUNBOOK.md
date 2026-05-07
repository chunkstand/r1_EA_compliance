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

## 5. Adjudicate Reviewer Worklist Items

Export the reviewer worklist when the intake or generated package has unresolved resource areas,
missing evidence refs, unknown resource-area IDs, calibration gaps, or optional deliverable
decisions:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-template \
  --intake /tmp/new_land_exchange_intake.json \
  --output-dir /tmp/project_sow_adjudication
```

The command writes a canonical `project_sow_adjudication_template.json` plus a Markdown worklist.
Reviewers complete the JSON rows with one of `accepted`, `rejected`, `needs_information`, or
`out_of_scope`, plus rationale, reviewer identity, date, and decision source. Also set the
top-level `reviewer_metadata.review_status` to `complete` and fill `reviewed_by`, `reviewed_at`,
and `review_source`. Do not edit item IDs, item types, resource-area IDs, action-element IDs,
resource-scope IDs, optional deliverable text, current status, selected SOW scopes, or source-check
fields; those values are current-queue identity fields and eval will fail if they drift.

Evaluate a completed adjudication artifact before replay:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-eval \
  --intake /tmp/new_land_exchange_intake.json \
  --adjudication /tmp/completed_project_sow_adjudication.json
```

Replay a passing adjudication into a new intake copy:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-apply \
  --intake /tmp/new_land_exchange_intake.json \
  --adjudication /tmp/completed_project_sow_adjudication.json \
  --output-intake /tmp/new_land_exchange_adjudicated_intake.json
```

Apply does not mutate the original intake and does not edit generated package outputs. It writes an
adjudicated intake copy with `project_sow_adjudication` replay metadata; regenerate the package from
that intake if the adjudication should appear in the reviewer snapshot and command summaries.

## 6. Add Calibration Reports When Available

If a completed example package exists, populate `observed_specialist_reports[]` with report title,
document role, source record ID, report ID, resource areas, and evidence refs.

Observed reports are calibration evidence only. They do not replace the proposed-action graph path:

```text
proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope
```

## 7. Validate The Intake

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

## 8. Generate The Package

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

## 9. Generate The EA Package Assembly Handoff

After `project_sow_package.json` is accepted, generate the downstream assembly checklist:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-ea-package-handoff \
  --package source_library/projects/<project_id>/requirements_package/project_sow_package.json
```

The command writes `project_sow_ea_package_handoff.json` and
`project_sow_ea_package_handoff.md` next to the package by default. It reads only the canonical
package JSON plus `config/project_sow_ea_handoff_rules_v1.json`; it does not inspect or require
future EA package files. The handoff maps selected SOW scopes into expected future slots for source
collection, specialist report production, public involvement, consultation, Forest Plan
consistency, and decision-record support.

The JSON and Markdown include a downstream consumption contract. Future commands may use the
package identity, input hashes, assembly categories, assembly slots, and downstream boundaries, but
must not infer that expected artifacts exist, are sufficient, are reviewer-ready, decide authority
applicability, justify generated rule-pack creation, or create compliance/legal conclusions.

Every handoff slot has `future_artifact_required_now=false`. The output is an assembly checklist,
not an applicability review, generated rule pack, compliance review, legal advice, legal sufficiency
conclusion, or final agency decision.

## 10. Run The Operational Gate

Before closing the project-SOW operationalization lane, run the local-only Operational Gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-operational-gate \
  --output-dir source_library/project_sow_operational_gate
```

The gate writes `project_sow_operational_gate_summary.json` and
`project_sow_operational_readiness_report.md` under the selected output directory. It validates the
minimal template and proving intakes without writing package outputs, runs `project-sow-eval`,
checks package/rendering smoke signals, generates an East Crazies EA handoff smoke artifact, and
verifies tracked JSON/docs references. The command is local-only for this sequence and should not be
treated as CI policy until a separate milestone adds CI integration.

## 11. Resolve Validation Failures

Common failure categories:

- required intake fields are missing;
- the intake schema version is unsupported;
- nested action element, evidence ref, federal land action, resource expectation, or observed
  report rows are missing required schema fields;
- drafted intake metadata still requires reviewer confirmation;
- a land-exchange intake has no federal land action;
- resource areas do not resolve to a configured SOW scope;
- project-SOW adjudication rows are pending, stale, duplicated, unexpected, missing, or carry an
  invalid decision, changed queue identity field, or incomplete top-level reviewer metadata;
- selected SOW scopes lack required contract fields such as assumptions, dependencies, acceptance
  criteria, reviewer role, review timing, optional deliverables, or reviewer signoff fields;
- selected SOW scopes lack required deliverables, even if optional deliverables are present;
- EA package handoff rules are missing required assembly categories, category metadata, expected
  future artifact types, category-rule scope/resource-area bindings, downstream boundaries, or
  future-artifact slot content;
- an action element has resource areas but no evidence refs;
- an action element has evidence refs but no resource areas;
- observed reports cover resource areas not derived from the proposed action;
- proposed-action or observed-report resource areas lack the canonical graph path;
- graph node or edge IDs collide before graph assembly;
- required Markdown or PDF rendering sections are missing.

Do not edit generated `source_library/` outputs by hand. Fix the intake or the tracked resource
scope config, then rerun the command.
