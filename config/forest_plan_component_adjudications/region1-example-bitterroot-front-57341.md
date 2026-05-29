# Forest Plan Component Adjudication Worklist

- Review ID: region1-example-bitterroot-front-57341
- Source set ID: source-set-f70ea11e04ae3d53
- Queue items: 20
- Pending items: 0
- JSON adjudication: config/forest_plan_component_adjudications/region1-example-bitterroot-front-57341.json
- Primary package evidence: EA-PACKAGE-002 Appendix D Forest Plan Consistency
- Scope evidence: Bitterroot Front package authority and selected-action forest-plan consistency worksheet

Resolved disposition counts:

- `applicability_false_positive`: 12
- `evidence_linking_miss`: 8

## Classification Rules

- Package-supported forest-plan consistency rows are `evidence_linking_miss` because project-specific evidence exists but the component run did not attach package evidence.
- A-P Wilderness, outfitter, fishless-water, cabin, campsite, and user-built-trail rows absent from the Bitterroot Front selected-action consistency evidence are `applicability_false_positive` because the queue overstates project scope for this package.
- No item is classified as a `true_ea_omission`; this replay closes the reviewer worklist as system classification/linking cleanup, not as a reviewer-ready promotion finding.

## Standard Queue Items

### FOR-006-MAINTENANCE-REHABILITATION-CABIN-USE-MECHANIZED-TOOLS-DONE-FASHION-MEETS-STANDARDS-MANAGEMENT-HISTOIIC-8FA5F30F-STD-1

- Disposition: `applicability_false_positive`
- Source type: `bitterroot_front_package_scope_review`
- Rationale: The Bitterroot Front package authority is the selected-action forest-plan consistency worksheet and project file; this A-P Wilderness, outfitter, fishless-water, cabin, campsite, or user-built-trail component is not supported as an applicable selected-action row, so the automatic applicability queue overstates project scope.

### FOR-006-FW-STD-VEG-01

- Disposition: `evidence_linking_miss`
- Source type: `bitterroot_front_forest_plan_consistency_replay`
- Rationale: Appendix D states project design features comply with the old-growth retention standard, but the current standard coverage artifact leaves FW-STD-VEG-01 as a gap.
