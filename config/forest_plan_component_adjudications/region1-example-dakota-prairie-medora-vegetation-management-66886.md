# Forest Plan Component Adjudication

- Review ID: region1-example-dakota-prairie-medora-vegetation-management-66886
- Source set ID: source-set-f70ea11e04ae3d53
- Current queue items: 384
- Resolved items: 384
- Pending items: 0
- Disposition counts: evidence_linking_miss=384
- JSON artifact: config/forest_plan_component_adjudications/region1-example-dakota-prairie-medora-vegetation-management-66886.json
- Adjudicated at: 2026-05-31T15:10:00Z

Method: `dakota_prairie_medora_nfma_consistency_decision_replay`

Primary package evidence:

- `EA-PACKAGE-001` decision record: NFMA finding says the responsible official evaluated the decision against Grasslands Plan goals, objectives, standards, and guidelines; found consistency with listed management areas and the Badlands/Rolling Prairie Geographic Areas; and found conformance with standards and appropriate guideline incorporation.
- `EA-PACKAGE-003` Medora DNA proposed action: purpose, need, design features, monitoring, and adaptive management for the vegetation-management action.
- `EA-PACKAGE-005` Pastures 4 and 6 EA: Grasslands Plan direction, design features, resource effects, FONSI consistency language, and response-to-comments support.

Resolved queue summary:

- Queue reasons: missing_package_evidence=384
- Component types: goal=8, guideline=219, objective=1, standard=156
- Direct package-evidence findings outside this queue: 10 supported findings now resolve during `forest-plan-resolve` after Dakota profile vocabulary expansion.
- Classification rule: all current queue items are `evidence_linking_miss` because the signed decision-record NFMA consistency finding and associated package analysis exist, but the current component-linking run did not attach that decision-record package evidence to the component findings.
- No item is classified as `true_ea_omission`; applicability, compliance review, and review phase-eval are now green locally, but downstream promotion still requires tracked V1 eval, tracked component eval, coverage, and registry promotion gates.

The JSON artifact contains the full current 384-item adjudication with per-item rationale and current-finding expectation locks.
