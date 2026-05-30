# Forest Plan Component Adjudication Worklist

- Review ID: region1-example-idaho-panhandle-lacy-lemoosh-60853
- Source set ID: source-set-f70ea11e04ae3d53
- Queue items: 36
- Pending items: 0
- JSON adjudication: config/forest_plan_component_adjudications/region1-example-idaho-panhandle-lacy-lemoosh-60853.json
- Primary package evidence: EA-PACKAGE-040 May 2025 Forest Plan Consistency Worksheet
- Scope evidence: Lacy Lemoosh package worksheet, Final EA, and specialist reports

Resolved disposition counts:

- `applicability_false_positive`: 10
- `component_inventory_overreach`: 1
- `evidence_linking_miss`: 25

## Classification Rules

- Positive and neutral worksheet responses are `evidence_linking_miss` because project-specific consistency evidence exists but the current component run left the row in the reviewer queue.
- Worksheet `not applicable` rows are `applicability_false_positive` because the automatic component scope overstates the Lacy Lemoosh project package.
- `FOR-021-max-2009` is `component_inventory_overreach` because it is a selected-status artifact, not a forest-plan component row.
- No item is classified as a `true_ea_omission`; this replay closes the current component worklist as system classification/linking cleanup while reviewer-stack replay remains a later gate.

## Current Standard Queue Items

### FOR-021-FW-STD-VEG-01

- Disposition: `evidence_linking_miss`
- Queue reason: `missing_package_evidence`
- Source type: `lacy_lemoosh_forest_plan_consistency_worksheet_replay`
- Rationale: The Lacy Lemoosh forest-plan consistency worksheet contains a non-not-applicable response for
  FW-STD-VEG-01; the current queue is missing or under-linking package evidence, not identifying a
  real EA omission.

### FOR-021-FW-STD-WTR-01

- Disposition: `applicability_false_positive`
- Queue reason: `missing_package_evidence`
- Source type: `lacy_lemoosh_package_scope_review`
- Rationale: The Lacy Lemoosh forest-plan consistency worksheet marks FW-STD-WTR-01 not applicable for this
  project scope, so the current reviewer queue overstates component applicability.

### FOR-021-FW-STD-IRA-01

- Disposition: `applicability_false_positive`
- Queue reason: `missing_package_evidence`
- Source type: `lacy_lemoosh_package_scope_review`
- Rationale: The Lacy Lemoosh forest-plan consistency worksheet marks FW-STD-IRA-01 not applicable for this
  project scope, so the current reviewer queue overstates component applicability.

### FOR-021-FW-STD-MIN-01

- Disposition: `applicability_false_positive`
- Queue reason: `missing_package_evidence`
- Source type: `lacy_lemoosh_package_scope_review`
- Rationale: The Lacy Lemoosh forest-plan consistency worksheet marks FW-STD-MIN-01 not applicable for this
  project scope, so the current reviewer queue overstates component applicability.

### FOR-021-max-2009

- Disposition: `component_inventory_overreach`
- Queue reason: `missing_package_evidence`
- Source type: `lacy_lemoosh_component_inventory_review`
- Rationale: The component inventory retained a selected-status artifact as Standard (max) 2009; it is not an
  Idaho Panhandle forest-plan component or a Lacy Lemoosh worksheet row.
